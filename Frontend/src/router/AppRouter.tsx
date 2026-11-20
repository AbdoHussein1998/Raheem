import { createBrowserRouter } from "react-router-dom";
import MainLayout from "../components/layout/MainLayout";
import { HomePage } from "../pages/HomePage";
import { Unauthorized } from "../pages/Unauthorized";
import { Usedup } from "../pages/Usedup";
import { NotFoundPage } from "../pages/NotFoundPage";
import { RouteErrorPage } from "../pages/RouteErrorPage";

/**
 * Application routes.
 *
 * Nginx handles the root "/" route:
 * - Missing UUID -> /unauthorized
 * - Provided UUID -> /api/redirect
 *
 * NestJS validates the UUID and redirects to:
 * - /app          -> Authorized application
 * - /unauthorized -> Invalid UUID
 * - /usedup       -> Insufficient quota
 */
export const router = createBrowserRouter([
  {
    path: "/",
    element: <MainLayout />,
    errorElement: <RouteErrorPage />,
    children: [
      {
        path: "app",
        element: <HomePage />,
      },
      {
        path: "unauthorized",
        element: <Unauthorized />,
      },
      {
        path: "usedup",
        element: <Usedup />,
      },
      {
        path: "*",
        element: <NotFoundPage />,
      },
    ],
  },
]);
