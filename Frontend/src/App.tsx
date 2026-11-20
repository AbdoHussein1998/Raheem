import { RouterProvider } from "react-router-dom";
import { router } from "./router/AppRouter";

/** Application composition: route configuration and layout live in their own modules. */
export default function App() {
  return <RouterProvider router={router} />;
}
