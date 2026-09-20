import { beforeEach, describe, expect, it, vi } from "vitest";

import { setupModelConfig } from "@/setupModelConfig.js";

const mocks = vi.hoisted(() => ({
    setConfig: vi.fn(),
}));

vi.mock("@vueda/stores/storeModelConfig.js", () => ({
    storeModelConfig: () => ({ setConfig: mocks.setConfig }),
}));

describe("setupModelConfig", () => {
    beforeEach(() => {
        mocks.setConfig.mockClear();
    });

    it("expands WidgetVariant and InventoryRecord foreign keys only in list views", () => {
        setupModelConfig({});

        const callsByModel = Object.fromEntries(
            mocks.setConfig.mock.calls.map(([target, genericConfig, viewConfigs]) => [
                target.model,
                { genericConfig, viewConfigs },
            ]),
        );

        expect(callsByModel.widgetvariant).toEqual({
            genericConfig: { expand: [] },
            viewConfigs: {
                list: {
                    expand: ["widget"],
                    expandDetails: {
                        widget: {
                            formatted: "widget.formatted_name",
                            value: "widget.id",
                        },
                    },
                },
            },
        });
        expect(callsByModel.inventoryrecord).toEqual({
            genericConfig: { expand: [] },
            viewConfigs: {
                list: {
                    expand: ["variant", "warehouse"],
                    expandDetails: {
                        variant: {
                            formatted: "variant.formatted_name",
                            value: "variant.id",
                        },
                        warehouse: {
                            formatted: "warehouse.formatted_name",
                            value: "warehouse.id",
                        },
                    },
                    displayFields: [
                        "formatted_name",
                        "quantity_on_hand",
                        "reorder_threshold",
                        "shortfall",
                        "max_stock_level",
                        "last_stocktake_at",
                        "last_received_at",
                        "notes",
                    ],
                },
            },
        });
    });

    it("identifies inventory by SKU and exposes the shortfall beside stock quantities", () => {
        setupModelConfig({});
        const [, , views] = mocks.setConfig.mock.calls.find(([target]) => target.model === "inventoryrecord");
        expect(views.list.displayFields).toContain("formatted_name");
        expect(views.list.displayFields).toContain("shortfall");
    });

    it("renders the Supplier notification addresses through FieldSetMany and keeps them off the list", () => {
        setupModelConfig({});

        const [, genericConfig, viewConfigs] = mocks.setConfig.mock.calls.find(
            ([target]) => target.model === "supplier",
        );

        expect(genericConfig).toEqual({
            fieldComponents: { notification_emails: "FieldSetMany" },
        });
        expect(viewConfigs.list.displayFields).not.toContain("notification_emails");
        expect(viewConfigs.list.fetchFields).toEqual(viewConfigs.list.displayFields);
    });

    it("limits the Widget list to scannable columns and fetches only those", () => {
        setupModelConfig({});

        const [, , viewConfigs] = mocks.setConfig.mock.calls.find(([target]) => target.model === "widget");

        expect(viewConfigs.list.displayFields).toEqual([
            "name",
            "sku",
            "category",
            "supplier",
            "unit_price",
            "weight_kg",
            "is_active",
            "release_date",
            "updated_at",
        ]);
        expect(viewConfigs.list.fetchFields).toEqual(viewConfigs.list.displayFields);
    });

    it("keeps the PurchaseOrder total_value column in the list so its server total can render", () => {
        setupModelConfig({});

        const [, , viewConfigs] = mocks.setConfig.mock.calls.find(([target]) => target.model === "purchaseorder");

        // The server declares total_value in column_totals, but ViewList renders the totals
        // row cell by cell across the displayed fields and reads each total by field name.
        // Drop the column and the total is in the response and nowhere on the page.
        expect(viewConfigs.list.displayFields).toContain("total_value");
        expect(viewConfigs.list.fetchFields).toEqual(viewConfigs.list.displayFields);
        // The lines stay out of the list: the value column is what the order is worth,
        // which is the reason the rows were expensive to show.
        expect(viewConfigs.list.displayFields).not.toContain("lines");
    });
});
