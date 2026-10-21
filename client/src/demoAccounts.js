export const DEMO_PASSWORD = "widget-demo";

export const DEMO_ACCOUNTS = [
    {
        role: "Inventory clerk",
        email: "clerk@widgetwarehouse.com",
        description:
            "Browse catalog, inventory, and warehouses; maintain suppliers and supplier prices; create purchase orders, update drafts, and submit them for approval.",
    },
    {
        role: "Inventory supervisor",
        email: "supervisor@widgetwarehouse.com",
        description:
            "Everything the clerk can do; update inventory counts and targets; update orders in any state; approve, reject, receive, or cancel orders; delete orders, suppliers, and supplier prices.",
    },
    {
        role: "Sales associate",
        email: "associate@widgetwarehouse.com",
        description: "Browse catalog, inventory, warehouses, and promotions without changing records.",
    },
    {
        role: "Sales manager",
        email: "manager@widgetwarehouse.com",
        description: "The same read-only access as the sales associate.",
    },
    {
        role: "Accountant",
        email: "accountant@widgetwarehouse.com",
        description:
            "Browse all catalog models and purchasing reports, without changing records or running transitions.",
    },
];
