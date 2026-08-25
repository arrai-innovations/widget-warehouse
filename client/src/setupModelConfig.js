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

    modelConfigStore.setConfig(
        { app: "catalog", model: "purchaseorder" },
        {
            // Expand the lines everywhere and nothing else. An expanded foreign key renders
            // as a subform of the related object's own fields, which is not what a supplier
            // picker should be; unexpanded, it stays a select of suppliers.
            expand: ["lines"],
            // Lines keep the inferred FieldSetStackedInline. A tabular inline is the better
            // shape for line items and is a one-line override
            // (fieldComponents: { lines: "FieldSetTabularInline" }), but VUEDA's tabular
            // inline currently renders its column header labels as commented-out markup, so
            // the columns come out unnamed. Stacked rows are taller and labelled.
        },
        {
            // The create, update, and read views take the expand above, so they carry the
            // inline. The list instead expands the two foreign keys, so their columns show a
            // name rather than an id, and drops the lines: displayed they are a cell full of
            // row ids, and fetched they cost a query per row for a column nobody reads.
            list: {
                displayFields: [
                    "reference",
                    "supplier",
                    "destination_warehouse",
                    "order_date",
                    "expected_arrival_date",
                    "created_at",
                    "updated_at",
                ],
                fetchFields: [
                    "reference",
                    "supplier",
                    "destination_warehouse",
                    "order_date",
                    "expected_arrival_date",
                    "created_at",
                    "updated_at",
                ],
                expand: ["supplier", "destination_warehouse"],
                expandDetails: {
                    supplier: {
                        formatted: "supplier.formatted_name",
                        value: "supplier.id",
                    },
                    destination_warehouse: {
                        formatted: "destination_warehouse.formatted_name",
                        value: "destination_warehouse.id",
                    },
                },
            },
        },
    );
}
