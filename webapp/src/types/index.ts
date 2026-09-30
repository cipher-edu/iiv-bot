export type UserRole = "citizen" | "officer" | "moderator" | "admin" | "superadmin";

export interface UserProfile {
  id: number;
  telegramId: number;
  fullName: string;
  username?: string;
  phone: string;
  role: UserRole;
  organization?: string;
  position?: string;
  rank?: string;
  avatarUrl?: string;
  streakDays: number;
  points: number;
  completedCoursesCount: number;
  certificatesCount: number;
  isBanned: boolean;
  banUntil?: string;
  category?: "hodim" | "fuqaro" | null;
  registered?: boolean;
}

export interface LessonAttachment {
  id: string;
  title: string;
  type: "pdf" | "video" | "audio" | "link";
  url: string;
  size?: string;
}

export interface Lesson {
  id: string;
  title: string;
  order: number;
  durationMinutes: number;
  content: string;
  videoUrl?: string;
  attachments?: LessonAttachment[];
  isCompleted?: boolean;
}

export interface CourseModule {
  id: string;
  title: string;
  order: number;
  lessons: Lesson[];
}

export interface Course {
  id: string;
  title: string;
  category: string;
  description: string;
  coverImage: string;
  syllabusFiles?: { id: string; title: string; url: string; type: string }[];
  instructor: string;
  durationHours: number;
  lessonsCount: number;
  studentsCount: number;
  rating: number;
  reviewsCount: number;
  status: "published" | "draft" | "archived";
  modules: CourseModule[];
  progressPercentage?: number;
}

export interface AnswerOption {
  id: string;
  text: string;
  isCorrect: boolean;
}

export interface Question {
  id: string;
  text: string;
  options: AnswerOption[];
  explanation?: string;
  points: number;
}

export interface TestItem {
  id: string;
  courseId?: string;
  courseTitle?: string;
  moduleTitle?: string;
  lessonTitle?: string;
  title: string;
  description: string;
  durationMinutes: number;
  passPercentage: number;
  questionsCount: number;
  totalAttemptsAllowed: number;
  userBestScore?: number;
  questions: Question[];
}

export interface LeaderboardUser {
  rank: number;
  id: number;
  fullName: string;
  organization?: string;
  points: number;
  streakDays: number;
  badge?: string;
  avatarUrl?: string;
}

export interface Certificate {
  id: string;
  certificateNumber: string;
  courseId: string;
  courseTitle: string;
  issueDate: string;
  studentName: string;
  organization?: string;
  scorePercentage: number;
  qrCodeUrl: string;
}

export interface BadgeItem {
  id: string;
  name: string;
  description: string;
  icon: string;
  isUnlocked: boolean;
  unlockedAt?: string;
}

export interface ChatMessage {
  id: string;
  sender: "user" | "ai";
  text: string;
  timestamp: string;
}
