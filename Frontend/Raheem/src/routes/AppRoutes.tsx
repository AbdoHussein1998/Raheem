import { Route, Routes } from "react-router-dom";
import MainLayout from "../components/layout/MainLayout";
import HomePage from "../pages/HomePage";
import GatewayPage from "../pages/GatewayPage";
import NotFoundPage from "../pages/NotFoundPage";

/** Public routes share a layout; the routed page renders at its Outlet. */
export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route index element={<HomePage />} />
        <Route path=":slug" element={<GatewayPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
