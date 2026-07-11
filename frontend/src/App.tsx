import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { ToastProvider } from "./components/Toast";
import { AppLayout } from "./layout/AppLayout";
import { About } from "./pages/About";
import { Alerts } from "./pages/Alerts";
import { Control } from "./pages/Control";
import { Environment } from "./pages/Environment";
import { HeaterAnalytics } from "./pages/HeaterAnalytics";
import { History } from "./pages/History";
import { IncubationProfile } from "./pages/IncubationProfile";
import { Overview } from "./pages/Overview";
import { PowerManagement } from "./pages/PowerManagement";
import { Settings } from "./pages/Settings";
import { ServoAnalytics } from "./pages/ServoAnalytics";
import { System } from "./pages/System";
import { SystemHealth } from "./pages/SystemHealth";

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <Overview /> },
      { path: "incubation", element: <IncubationProfile /> },
      { path: "environment", element: <Environment /> },
      { path: "control", element: <Control /> },
      { path: "servo", element: <ServoAnalytics /> },
      { path: "heater", element: <HeaterAnalytics /> },
      { path: "power", element: <PowerManagement /> },
      { path: "system-health", element: <SystemHealth /> },
      { path: "history", element: <History /> },
      { path: "alerts", element: <Alerts /> },
      { path: "settings", element: <Settings /> },
      { path: "system", element: <System /> },
      { path: "about", element: <About /> }
    ]
  }
]);

export function App() {
  return (
    <ToastProvider>
      <RouterProvider router={router} />
    </ToastProvider>
  );
}
