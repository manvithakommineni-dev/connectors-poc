import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import SalesforceExplorer from "./pages/SalesforceExplorer";
import HubspotExplorer from "./pages/HubspotExplorer";
import SAPExplorer from "./pages/SAPExplorer";
import OracleExplorer from "./pages/OracleExplorer";
import WorkdayExplorer from "./pages/WorkdayExplorer";
import ServiceNowExplorer from "./pages/ServiceNowExplorer";
import NetSuiteExplorer from "./pages/NetSuiteExplorer";
import { GoogleAdsExplorer } from "./pages/GoogleAdsExplorer";
import { GA4Explorer } from "./pages/GA4Explorer";
import { MetaAdsExplorer } from "./pages/MetaAdsExplorer";
import { AdjustExplorer } from "./pages/AdjustExplorer";
import { WorkatoExplorer } from "./pages/WorkatoExplorer";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 1000 * 60 * 5, retry: 1 },
  },
});

type Connector = "salesforce" | "hubspot" | "sap" | "oracle" | "workday" | "servicenow" | "netsuite" | "googleads" | "ga4" | "metaads" | "adjust" | "workato";

const CONNECTORS: { id: Connector; label: string; color: string; bg: string }[] = [
  { id: "salesforce",  label: "Salesforce",  color: "#60a5fa", bg: "#1e3a5f" },
  { id: "hubspot",     label: "HubSpot",     color: "#fb923c", bg: "#431407" },
  { id: "sap",         label: "SAP",         color: "#c084fc", bg: "#1a0a2e" },
  { id: "oracle",      label: "Oracle",      color: "#f87171", bg: "#3b0a0a" },
  { id: "workday",     label: "Workday",     color: "#60c8ff", bg: "#0a2540" },
  { id: "servicenow",  label: "ServiceNow",  color: "#a78bfa", bg: "#1e0a3c" },
  { id: "netsuite",    label: "NetSuite",    color: "#fb923c", bg: "#2d1200" },
  { id: "googleads",   label: "Google Ads",  color: "#4ade80", bg: "#052e16" },
  { id: "ga4",         label: "GA4",         color: "#fbbf24", bg: "#422006" },
  { id: "metaads",     label: "Meta Ads",    color: "#60a5fa", bg: "#1e3a5f" },
  { id: "adjust",      label: "Adjust",      color: "#34d399", bg: "#064e3b" },
  { id: "workato",     label: "Workato",     color: "#a78bfa", bg: "#2e1065" },
];

function App() {
  const [active, setActive] = useState<Connector>("salesforce");

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "#0f172a" }}>
      {/* Connector selector nav */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "8px 20px",
          background: "#020617",
          borderBottom: "1px solid #1e293b",
        }}
      >
        <span style={{ fontSize: 12, color: "#475569", marginRight: 4, fontWeight: 600 }}>
          CONNECTOR
        </span>
        {CONNECTORS.map((c) => (
          <button
            key={c.id}
            onClick={() => setActive(c.id)}
            style={{
              padding: "4px 16px",
              borderRadius: 20,
              border: "none",
              cursor: "pointer",
              fontSize: 12,
              fontWeight: 600,
              background: active === c.id ? c.bg : "#1e293b",
              color: active === c.id ? c.color : "#64748b",
              transition: "all 0.15s",
            }}
          >
            {c.label}
          </button>
        ))}
      </div>

      {/* Active connector view */}
      <div style={{ flex: 1, overflow: "hidden" }}>
        {active === "salesforce" && <SalesforceExplorer />}
        {active === "hubspot"    && <HubspotExplorer />}
        {active === "sap"        && <SAPExplorer />}
        {active === "oracle"     && <OracleExplorer />}
        {active === "workday"    && <WorkdayExplorer />}
        {active === "servicenow" && <ServiceNowExplorer />}
        {active === "netsuite"   && <NetSuiteExplorer />}
        {active === "googleads"  && <GoogleAdsExplorer />}
        {active === "ga4"        && <GA4Explorer />}
        {active === "metaads"    && <MetaAdsExplorer />}
        {active === "adjust"     && <AdjustExplorer />}
        {active === "workato"   && <WorkatoExplorer />}
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>
);
