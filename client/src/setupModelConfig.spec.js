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
                },
            },
        });
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
});
