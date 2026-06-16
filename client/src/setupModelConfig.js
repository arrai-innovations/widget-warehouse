import { storeModelConfig } from "@vueda/stores/storeModelConfig.js";

export function setupModelConfig(pinia) {
    const modelConfigStore = storeModelConfig(pinia);

    modelConfigStore.setConfig(
        { app: "catalog", model: "widget" },
        {
            expand: [],
        },
        {
            list: {
                expand: ["category", "supplier"],
                expandDetails: {
                    category: {
                        formatted: "category.formatted_name",
                        value: "category.id",
                    },
                    supplier: {
                        formatted: "supplier.formatted_name",
                        value: "supplier.id",
                    },
                },
            },
        },
    );
}
