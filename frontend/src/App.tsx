import { useEffect, lazy, Suspense, useMemo } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, Spin } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { getAntTheme } from './theme';
import { useThemeStore } from './stores/themeStore';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Login from './pages/Login';
import MainLayout from './components/layout/MainLayout';
import ErrorBoundary from './components/ErrorBoundary';
import { useAuthStore } from './stores/authStore';

// 路由懒加载
const Dashboard = lazy(() => import('./pages/dashboard/Dashboard'));
const StudentList = lazy(() => import('./pages/students/StudentList'));
const StudentImport = lazy(() => import('./pages/students/import/StudentImport'));
const StudentReport = lazy(() => import('./pages/students/StudentReport'));
const SupervisionLogList = lazy(() => import('./pages/supervision/SupervisionLogList'));
const CourseList = lazy(() => import('./pages/courses/CourseList'));
const HomeworkList = lazy(() => import('./pages/homework/HomeworkList'));
const CheckinPage = lazy(() => import('./pages/checkins/CheckinPage'));
const PositionList = lazy(() => import('./pages/positions/PositionList'));
const GuokaoPositionList = lazy(() => import('./pages/positions/GuokaoPositionList'));
const ShiyePositionList = lazy(() => import('./pages/positions/ShiyePositionList'));
const PositionImport = lazy(() => import('./pages/positions/PositionImport'));
const AuditLogList = lazy(() => import('./pages/audit/AuditLogList'));
const StudyPlanList = lazy(() => import('./pages/studyPlans/StudyPlanList'));
const StudyPlanDetail = lazy(() => import('./pages/studyPlans/StudyPlanDetail'));
const ClassBatchList = lazy(() => import('./pages/courseRecordings/ClassBatchList'));
const CourseRecordingList = lazy(() => import('./pages/courseRecordings/CourseRecordingList'));
const MistakeList = lazy(() => import('./pages/mistakes/MistakeList'));
const QuestionList = lazy(() => import('./pages/questions/QuestionList'));
const WorkbookList = lazy(() => import('./pages/questions/WorkbookList'));
const PackageList = lazy(() => import('./pages/packages/PackageList'));
const AttendanceList = lazy(() => import('./pages/attendances/AttendanceList'));
const StudentRecommend = lazy(() => import('./pages/students/StudentRecommend'));
const ExamPaperList = lazy(() => import('./pages/examPapers/ExamPaperList'));
const ExamScoreList = lazy(() => import('./pages/examScores/ExamScoreList'));
const AIImportPage = lazy(() => import('./pages/aiImport/AIImportPage'));
const ClassAnalysisPage = lazy(() => import('./pages/classAnalysis/ClassAnalysisPage'));
const FinancePage = lazy(() => import('./pages/finance/FinancePage'));
const UserList = lazy(() => import('./pages/users/UserList'));
const StudentDetail = lazy(() => import('./pages/students/StudentDetail'));
const SettingsPage = lazy(() => import('./pages/settings/SettingsPage'));
const NotificationList = lazy(() => import('./pages/notifications/NotificationList'));
const CalendarPage = lazy(() => import('./pages/calendar/CalendarPage'));
const ProfilePage = lazy(() => import('./pages/profile/ProfilePage'));
const RecycleBinPage = lazy(() => import('./pages/recycleBin/RecycleBinPage'));
const RecruitmentInfoList = lazy(() => import('./pages/recruitmentInfo/RecruitmentInfoList'));
const CrawlerManagement = lazy(() => import('./pages/recruitmentInfo/CrawlerManagement'));
const SubmitMistakes = lazy(() => import('./pages/submit/SubmitMistakes'));
const MobileCheckin = lazy(() => import('./pages/checkinMobile/MobileCheckin'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const PageLoader = () => (
  <div style={{ textAlign: 'center', padding: 60 }}><Spin size="large" /></div>
);

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuthStore();
  if (loading) return <div className="flex h-screen items-center justify-center"><Spin size="large" /></div>;
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <>{children}</>;
}

function App() {
  const fetchUser = useAuthStore((state) => state.fetchUser);
  const themeMode = useThemeStore((state) => state.mode);
  const antTheme = useMemo(() => getAntTheme(themeMode), [themeMode]);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  // 初始化主题属性
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', themeMode);
  }, [themeMode]);

  // Ensure static message/modal/notification can consume current theme context.
  useEffect(() => {
    ConfigProvider.config({
      holderRender: (children) => (
        <ConfigProvider locale={zhCN} theme={antTheme}>
          {children}
        </ConfigProvider>
      ),
    });
  }, [antTheme]);

  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider locale={zhCN} theme={antTheme}>
        <ErrorBoundary>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
            <Route path="/submit/:token" element={<Suspense fallback={<PageLoader />}><SubmitMistakes /></Suspense>} />
            <Route path="/checkin/:token" element={<Suspense fallback={<PageLoader />}><MobileCheckin /></Suspense>} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <MainLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Suspense fallback={<PageLoader />}><Dashboard /></Suspense>} />
              <Route path="students" element={<Suspense fallback={<PageLoader />}><StudentList /></Suspense>} />
              <Route path="students/import" element={<Suspense fallback={<PageLoader />}><StudentImport /></Suspense>} />
              <Route path="students/:id/recommend" element={<Suspense fallback={<PageLoader />}><StudentRecommend /></Suspense>} />
              <Route path="students/:id/report" element={<Suspense fallback={<PageLoader />}><StudentReport /></Suspense>} />
              <Route path="students/:id" element={<Suspense fallback={<PageLoader />}><StudentDetail /></Suspense>} />
              <Route path="supervision" element={<Suspense fallback={<PageLoader />}><SupervisionLogList /></Suspense>} />
              <Route path="courses" element={<Suspense fallback={<PageLoader />}><CourseList /></Suspense>} />
              <Route path="homework" element={<Suspense fallback={<PageLoader />}><HomeworkList /></Suspense>} />
              <Route path="checkins" element={<Suspense fallback={<PageLoader />}><CheckinPage /></Suspense>} />
              <Route path="positions" element={<Suspense fallback={<PageLoader />}><PositionList /></Suspense>} />
              <Route path="guokao-positions" element={<Suspense fallback={<PageLoader />}><GuokaoPositionList /></Suspense>} />
              <Route path="shiye-positions" element={<Suspense fallback={<PageLoader />}><ShiyePositionList /></Suspense>} />
              <Route path="positions/import" element={<Suspense fallback={<PageLoader />}><PositionImport /></Suspense>} />
              <Route path="audit-logs" element={<Suspense fallback={<PageLoader />}><AuditLogList /></Suspense>} />
              <Route path="study-plans" element={<Suspense fallback={<PageLoader />}><StudyPlanList /></Suspense>} />
              <Route path="study-plans/:id" element={<Suspense fallback={<PageLoader />}><StudyPlanDetail /></Suspense>} />
              <Route path="class-batches" element={<Suspense fallback={<PageLoader />}><ClassBatchList /></Suspense>} />
              <Route path="course-recordings" element={<Suspense fallback={<PageLoader />}><CourseRecordingList /></Suspense>} />
              <Route path="mistakes" element={<Suspense fallback={<PageLoader />}><MistakeList /></Suspense>} />
              <Route path="questions" element={<Suspense fallback={<PageLoader />}><QuestionList /></Suspense>} />
              <Route path="workbooks" element={<Suspense fallback={<PageLoader />}><WorkbookList /></Suspense>} />
              <Route path="packages" element={<Suspense fallback={<PageLoader />}><PackageList /></Suspense>} />
              <Route path="attendances" element={<Suspense fallback={<PageLoader />}><AttendanceList /></Suspense>} />
              <Route path="exam-papers" element={<Suspense fallback={<PageLoader />}><ExamPaperList /></Suspense>} />
              <Route path="exam-scores" element={<Suspense fallback={<PageLoader />}><ExamScoreList /></Suspense>} />
              <Route path="ai-import" element={<Suspense fallback={<PageLoader />}><AIImportPage /></Suspense>} />
              <Route path="class-analysis" element={<Suspense fallback={<PageLoader />}><ClassAnalysisPage /></Suspense>} />
              <Route path="finance" element={<Suspense fallback={<PageLoader />}><FinancePage /></Suspense>} />
              <Route path="users" element={<Suspense fallback={<PageLoader />}><UserList /></Suspense>} />
              <Route path="settings" element={<Suspense fallback={<PageLoader />}><SettingsPage /></Suspense>} />
              <Route path="notifications" element={<Suspense fallback={<PageLoader />}><NotificationList /></Suspense>} />
              <Route path="calendar" element={<Suspense fallback={<PageLoader />}><CalendarPage /></Suspense>} />
              <Route path="profile" element={<Suspense fallback={<PageLoader />}><ProfilePage /></Suspense>} />
              <Route path="recycle-bin" element={<Suspense fallback={<PageLoader />}><RecycleBinPage /></Suspense>} />
              <Route path="recruitment-info" element={<Suspense fallback={<PageLoader />}><RecruitmentInfoList /></Suspense>} />
              <Route path="crawler-management" element={<Suspense fallback={<PageLoader />}><CrawlerManagement /></Suspense>} />
            </Route>
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
        </ErrorBoundary>
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default App;
