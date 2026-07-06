export type Status = "todo" | "in_progress" | "review" | "done";
export type Priority = "low" | "medium" | "high" | "critical";

export type Member = {
  id: number;
  fullName: string;
  role: string;
  avatarUrl?: string;
  activeTasks: number;
  capacity: number;
};

export type Task = {
  id: number;
  key: string;
  title: string;
  description: string;
  status: Status;
  priority: Priority;
  assignee: Member;
  dueDate: string;
  comments: number;
  attachments: number;
  isBlocked?: boolean;
  blockedReason?: string;
  aiRiskScore: number;
  estimatedHours: number;
};

export type ProjectReport = {
  totalTasks: number;
  completedTasks: number;
  overdueTasks: number;
  blockedTasks: number;
  sprintHealthScore: number;
};
