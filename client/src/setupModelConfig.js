import { storeModelConfig } from "@vueda/stores/storeModelConfig.js";

export function setupModelConfig(pinia) {
    const modelConfigStore = storeModelConfig(pinia);

    modelConfigStore.setConfig(
        { app: "catalog", model: "widget" },
        {
            expand: [],
        },
        {
            // The list shows the columns an operator scans by. Slug, description, file fields,
            // the warranty duration, and the specifications JSON stay on the read view: in a
            // list they are mostly empty or raw, and they push the grid into horizontal scroll.
            list: {
                displayFields: [
                    "name",
                    "sku",
                    "category",
                    "supplier",
                    "unit_price",
                    "weight_kg",
                    "is_active",
                    "release_date",
                    "updated_at",
                ],
                fetchFields: [
                    "name",
                    "sku",
                    "category",
                    "supplier",
                    "unit_price",
                    "weight_kg",
                    "is_active",
                    "release_date",
                    "updated_at",
                ],
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

    // notification_emails is an ArrayField of EmailField, which VUEDA reports as a many
    // EmailField. No field type resolves to a FieldSet on its own: every field falls back
    // to FormField, and a many field would render as one text input holding the whole
    // list. Naming FieldSetMany here is what turns it into a row per address with add and
    // remove buttons, because field resolution reads fieldComponents before the type
    // mapping. The mapping still supplies the manyComponent each row is built from, which
    // is why this needs no fieldProps beside it. Delete the override to see the default.
    modelConfigStore.setConfig(
        { app: "catalog", model: "supplier" },
        {
            fieldComponents: { notification_emails: "FieldSetMany" },
        },
        {
            // A list cell has no many-aware column adapter, so an array lands on ColumnText
            // and prints as JSON. The addresses belong on the object, not in the grid.
            list: {
                displayFields: [
                    "name",
                    "contact_email",
                    "country",
                    "reliability_score",
                    "typical_lead_days",
                    "is_approved",
                    "is_active",
                ],
                fetchFields: [
                    "name",
                    "contact_email",
                    "country",
                    "reliability_score",
                    "typical_lead_days",
                    "is_approved",
                    "is_active",
                ],
            },
        },
    );

    modelConfigStore.setConfig(
        { app: "catalog", model: "widgetvariant" },
        {
            expand: [],
        },
        {
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
    );

    modelConfigStore.setConfig(
        { app: "catalog", model: "inventoryrecord" },
        {
            expand: [],
            fieldProps: {
                max_stock_level: { clearServerErrorDependents: ["quantity_on_hand"] },
            },
        },
        {
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
                // The record label identifies the SKU as well as its warehouse.
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
    );

    modelConfigStore.setConfig(
        { app: "catalog", model: "supplierprice" },
        { expand: [], displayFields: ["formatted_name", "unit_cost"] },
        {
            create: { displayFields: ["supplier", "variant", "unit_cost"] },
            update: { displayFields: ["supplier", "variant", "unit_cost"] },
        },
    );

    modelConfigStore.setConfig(
        { app: "catalog", model: "purchaseorder" },
        {
            fieldProps: {
                supplier: { clearServerErrorDependents: ["expected_arrival_date"] },
                order_date: { clearServerErrorDependents: ["expected_arrival_date"] },
            },
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
            //
            // "total_value" is the server's column_totals column, and it is listed here for
            // more than the column itself: ViewList draws the totals row by walking the
            // displayed fields and looking each total up by field name, so a total whose
            // column is not displayed is fetched and then never rendered.
            list: {
                displayFields: [
                    "reference",
                    "supplier",
                    "destination_warehouse",
                    "order_date",
                    "expected_arrival_date",
                    "total_value",
                    "created_at",
                    "updated_at",
                ],
                fetchFields: [
                    "reference",
                    "supplier",
                    "destination_warehouse",
                    "order_date",
                    "expected_arrival_date",
                    "total_value",
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
