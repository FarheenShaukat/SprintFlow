from django.db.models import Count
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activity.services import log_activity
from apps.core.permissions import WorkspaceRolePermission
from .models import Workspace, WorkspaceInvitation, WorkspaceMember
from .serializers import InvitationAcceptSerializer, WorkspaceInvitationSerializer, WorkspaceInviteSerializer, WorkspaceMemberSerializer, WorkspaceSerializer

User = get_user_model()


class WorkspaceViewSet(viewsets.ModelViewSet):
    serializer_class = WorkspaceSerializer
    permission_classes = [WorkspaceRolePermission]
    basename = "workspace"

    def get_queryset(self):
        return (
            Workspace.objects.filter(memberships__user=self.request.user)
            .select_related("owner")
            .annotate(member_count=Count("memberships"))
            .distinct()
        )

    def perform_create(self, serializer):
        workspace = serializer.save(owner=self.request.user)
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=self.request.user,
            role=WorkspaceMember.Role.OWNER,
        )
        log_activity(user=self.request.user, workspace=workspace, action="workspace.created", new_value=workspace.name)


class WorkspaceMemberViewSet(viewsets.ModelViewSet):
    serializer_class = WorkspaceMemberSerializer
    permission_classes = [WorkspaceRolePermission]

    def get_queryset(self):
        return WorkspaceMember.objects.filter(workspace_id=self.kwargs["workspace_id"]).select_related("user", "workspace")

    def _require_workspace_manager(self, workspace):
        role = WorkspaceMember.objects.filter(workspace=workspace, user=self.request.user).values_list("role", flat=True).first()
        if role not in {WorkspaceMember.Role.OWNER, WorkspaceMember.Role.ADMIN}:
            raise PermissionDenied("Only workspace owners or admins can manage members.")

    def perform_create(self, serializer):
        workspace = Workspace.objects.get(pk=self.kwargs["workspace_id"])
        self._require_workspace_manager(workspace)
        member = serializer.save(workspace=workspace)
        log_activity(
            user=self.request.user,
            workspace=workspace,
            action="member.added",
            new_value=f"{member.user.email}:{member.role}",
        )

    def perform_update(self, serializer):
        workspace = serializer.instance.workspace
        self._require_workspace_manager(workspace)
        member = serializer.save()
        log_activity(
            user=self.request.user,
            workspace=workspace,
            action="member.role_changed",
            new_value=f"{member.user.email}:{member.role}",
        )

    def perform_destroy(self, instance):
        workspace = instance.workspace
        self._require_workspace_manager(workspace)
        email = instance.user.email
        instance.delete()
        log_activity(
            user=self.request.user,
            workspace=workspace,
            action="member.removed",
            old_value=email,
        )


class WorkspaceInviteView(APIView):
    permission_classes = [WorkspaceRolePermission]

    def get(self, request, workspace_id):
        workspace = Workspace.objects.get(pk=workspace_id, memberships__user=request.user)
        role = WorkspaceMember.objects.filter(workspace=workspace, user=request.user).values_list("role", flat=True).first()
        if role == WorkspaceMember.Role.MEMBER:
            raise PermissionDenied("Only workspace owners or admins can view invitations.")
        invitations = WorkspaceInvitation.objects.filter(workspace=workspace).select_related("invited_by", "accepted_by")
        return Response({
            "count": invitations.count(),
            "next": None,
            "previous": None,
            "results": WorkspaceInvitationSerializer(invitations, many=True).data,
        })

    def post(self, request, workspace_id):
        serializer = WorkspaceInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        workspace = Workspace.objects.get(pk=workspace_id, memberships__user=request.user)
        role_for_inviter = WorkspaceMember.objects.filter(workspace=workspace, user=request.user).values_list("role", flat=True).first()
        if role_for_inviter == WorkspaceMember.Role.MEMBER and not workspace.allow_member_invite_members:
            raise PermissionDenied("Members are not allowed to invite people to this workspace.")

        email = serializer.validated_data["email"].lower()
        full_name = serializer.validated_data.get("full_name") or email.split("@")[0]
        role = serializer.validated_data["role"]
        invitation, _ = WorkspaceInvitation.objects.update_or_create(
            workspace=workspace,
            email=email,
            defaults={
                "full_name": full_name,
                "role": role,
                "status": WorkspaceInvitation.Status.PENDING,
                "invited_by": request.user,
                "accepted_by": None,
                "accepted_at": None,
                "email_sent": False,
                "email_error": "",
            },
        )

        accept_url = f"{settings.FRONTEND_URL.rstrip()}/invitations/{invitation.token}"
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;padding:24px;border:1px solid #e4e1ee;border-radius:12px">
          <h2 style="color:#3525cd;margin:0 0 12px">Join {workspace.name}</h2>
          <p>{request.user.full_name} invited you to join <strong>{workspace.name}</strong> as <strong>{role}</strong>.</p>
          <p>Click the button below to accept the invitation.</p>
          <a href="{accept_url}" style="display:inline-block;background:#3525cd;color:white;text-decoration:none;padding:12px 18px;border-radius:8px;font-weight:700">Join Workspace</a>
          <p style="font-size:12px;color:#464555;margin-top:20px">If the button does not work, open this link: {accept_url}</p>
        </div>
        """
        message = EmailMultiAlternatives(
            subject=f"Join {workspace.name} on SprintFlow AI",
            body=f"{request.user.full_name} invited you to join {workspace.name}. Accept: {accept_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        message.attach_alternative(html, "text/html")
        try:
            message.send()
            invitation.email_sent = True
            invitation.email_error = ""
        except Exception as exc:
            invitation.email_sent = False
            invitation.email_error = str(exc)
        invitation.save(update_fields=["email_sent", "email_error", "updated_at"])

        log_activity(
            user=request.user,
            workspace=workspace,
            action="member.invited",
            new_value=f"{email}:{role}",
        )
        return Response(WorkspaceInvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)


class InvitationAcceptView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        invitation = WorkspaceInvitation.objects.select_related("workspace").get(token=token)
        user = User.objects.filter(email=invitation.email).first()
        return Response({
            "email": invitation.email,
            "full_name": invitation.full_name,
            "workspace_id": invitation.workspace_id,
            "workspace_name": invitation.workspace.name,
            "status": invitation.status,
            "user_exists": bool(user and user.has_usable_password()),
        })

    def post(self, request, token):
        invitation = WorkspaceInvitation.objects.select_related("workspace").get(token=token)
        user, created = User.objects.get_or_create(
            email=invitation.email,
            defaults={"full_name": invitation.full_name or invitation.email.split("@")[0], "is_active": True},
        )
        if created:
            user.set_unusable_password()
            user.save(update_fields=["password"])
        invitation.accept(user)
        log_activity(
            user=user,
            workspace=invitation.workspace,
            action="member.invite_accepted",
            new_value=invitation.email,
        )
        return Response({
            "email": invitation.email,
            "full_name": invitation.full_name,
            "workspace_id": invitation.workspace_id,
            "workspace_name": invitation.workspace.name,
            "status": invitation.status,
            "user_exists": user.has_usable_password(),
        })
