import type { Member, Task } from "@/types/domain";

export const members: Member[] = [
  { id: 1, fullName: "Farheen K.", role: "Senior Frontend Engineer", activeTasks: 3, capacity: 60 },
  { id: 2, fullName: "Fatima A.", role: "Backend Engineer", activeTasks: 2, capacity: 40 },
  { id: 3, fullName: "Ali R.", role: "Product Designer", activeTasks: 8, capacity: 85 },
  { id: 4, fullName: "Sarah Chen", role: "QA Lead", activeTasks: 4, capacity: 55 }
];

export const tasks: Task[] = [
  {
    id: 1,
    key: "SFA-102",
    title: "Implement JWT Authentication",
    description: "Create secure register/login APIs, token refresh, protected routes, and tests.",
    status: "todo",
    priority: "critical",
    assignee: members[1],
    dueDate: "Tomorrow",
    comments: 6,
    attachments: 3,
    aiRiskScore: 84,
    estimatedHours: 5
  },
  {
    id: 2,
    key: "SFA-145",
    title: "Setup Redis Caching for User Sessions",
    description: "Add Redis cache configuration and session invalidation service.",
    status: "todo",
    priority: "medium",
    assignee: members[0],
    dueDate: "Jul 24",
    comments: 2,
    attachments: 1,
    aiRiskScore: 38,
    estimatedHours: 3
  },
  {
    id: 3,
    key: "SFA-201",
    title: "Refactor API Response Middleware",
    description: "Standardize DRF error responses and add request IDs to activity logs.",
    status: "in_progress",
    priority: "high",
    assignee: members[2],
    dueDate: "Today",
    comments: 12,
    attachments: 2,
    isBlocked: true,
    blockedReason: "Waiting for architectural review from backend lead.",
    aiRiskScore: 91,
    estimatedHours: 8
  },
  {
    id: 4,
    key: "SFA-220",
    title: "Mobile Responsive Layout fixes",
    description: "Polish mobile navigation and prevent task card overflow.",
    status: "in_progress",
    priority: "high",
    assignee: members[0],
    dueDate: "Jul 18",
    comments: 2,
    attachments: 0,
    aiRiskScore: 66,
    estimatedHours: 4
  },
  {
    id: 5,
    key: "SFA-248",
    title: "Database Migration Script v2",
    description: "Prepare Supabase PostgreSQL migrations and rollback notes.",
    status: "review",
    priority: "medium",
    assignee: members[3],
    dueDate: "In Review",
    comments: 5,
    attachments: 1,
    aiRiskScore: 52,
    estimatedHours: 6
  },
  {
    id: 6,
    key: "SFA-300",
    title: "Draft README architecture section",
    description: "Document stack, ERD, API docs, and deployment flow.",
    status: "done",
    priority: "low",
    assignee: members[0],
    dueDate: "Done",
    comments: 1,
    attachments: 0,
    aiRiskScore: 12,
    estimatedHours: 2
  }
];

export const report = {
  totalTasks: 58,
  completedTasks: 42,
  overdueTasks: 4,
  blockedTasks: 3,
  sprintHealthScore: 91
};
