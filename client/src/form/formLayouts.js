/**
 * Create and update form layouts, keyed by `app.model`, for `SectionedFormFields`.
 *
 * Each section lists field names with the columns each claims at and above FormGrid's
 * breakpoint, out of twelve. FormGrid stamps spans for 3, 4, 6, 8, and 9; anything else
 * stays full width. A row is filled left to right, so the spans in a section are written
 * to add up to twelve per intended row.
 *
 * The default create and update views look a model up here, so a model gets a layout by
 * gaining an entry and needs no view file of its own. A model with no entry keeps VUEDA's
 * one-field-per-row form.
 */
export const formLayouts = {
    "catalog.widgetcategory": [
        {
            title: "Category",
            fields: [
                ["code", 4],
                ["name", 8],
                ["description", 12],
            ],
        },
    ],
    "catalog.supplier": [
        {
            title: "Supplier",
            fields: [
                ["name", 6],
                ["slug", 3],
                ["country", 3],
            ],
        },
        {
            title: "Contact",
            aside: "orders are sent here",
            fields: [
                ["contact_email", 6],
                ["website", 6],
                ["notification_emails", 12],
            ],
        },
        {
            title: "Standing",
            aside: "lead time drives order warnings",
            fields: [
                ["reliability_score", 3],
                ["typical_lead_days", 3],
                ["is_approved", 3],
                ["is_active", 3],
            ],
        },
        {
            title: "Notes",
            fields: [["notes", 12]],
        },
        {
            title: "Record",
            aside: "server maintained",
            fields: [
                ["created_at", 6],
                ["updated_at", 6],
            ],
        },
    ],
    "catalog.widget": [
        {
            title: "Product",
            fields: [
                ["name", 6],
                ["sku", 3],
                ["slug", 3],
                ["category", 4],
                ["supplier", 4],
                ["is_active", 4],
                ["description", 12],
            ],
        },
        {
            title: "Pricing and shipping",
            fields: [
                ["unit_price", 3],
                ["weight_kg", 3],
                ["warranty_period", 3],
                ["release_date", 3],
            ],
        },
        {
            title: "Files",
            aside: "optional",
            fields: [
                ["image", 6],
                ["datasheet", 6],
            ],
        },
        {
            title: "Specifications",
            aside: "key and value pairs",
            fields: [["specifications", 12]],
        },
        {
            title: "Record",
            aside: "server maintained",
            fields: [
                ["created_at", 6],
                ["updated_at", 6],
            ],
        },
    ],
    "catalog.widgetvariant": [
        {
            title: "Variant",
            fields: [
                ["widget", 6],
                ["name", 3],
                ["sku_suffix", 3],
            ],
        },
        {
            title: "Price and stock",
            fields: [
                ["additional_price", 6],
                ["stock_quantity", 6],
            ],
        },
    ],
    "catalog.supplierprice": [
        {
            title: "Price",
            aside: "copied onto new order lines",
            fields: [
                ["supplier", 4],
                ["variant", 4],
                ["unit_cost", 4],
            ],
        },
    ],
    "catalog.warehouse": [
        {
            title: "Warehouse",
            fields: [
                ["name", 6],
                ["code", 3],
                ["is_active", 3],
                ["address", 12],
            ],
        },
        {
            title: "Contact and hours",
            fields: [
                ["contact_email", 6],
                ["opens_at", 3],
                ["closes_at", 3],
            ],
        },
        {
            title: "Record",
            aside: "server maintained",
            fields: [["uuid", 6]],
        },
    ],
    "catalog.inventoryrecord": [
        {
            title: "Location",
            aside: "one record per variant and warehouse",
            fields: [
                ["variant", 6],
                ["warehouse", 6],
            ],
        },
        {
            title: "Stock levels",
            fields: [
                ["quantity_on_hand", 3],
                ["reorder_threshold", 3],
                ["max_stock_level", 3],
                ["shortfall", 3],
            ],
        },
        {
            title: "Activity",
            fields: [
                ["last_stocktake_at", 6],
                ["last_received_at", 6],
                ["notes", 12],
            ],
        },
        {
            title: "Record",
            aside: "server maintained",
            fields: [["formatted_name", 6]],
        },
    ],
    "catalog.promotion": [
        {
            title: "Promotion",
            fields: [
                ["name", 6],
                ["code", 3],
                ["is_active", 3],
                ["description", 12],
            ],
        },
        {
            title: "Discount",
            fields: [
                ["discount_percent", 3],
                ["valid_dates", 9],
            ],
        },
        {
            title: "Widgets",
            aside: "the promotion applies to",
            fields: [["widgets", 12]],
        },
        {
            title: "Record",
            aside: "server maintained",
            fields: [["created_at", 6]],
        },
    ],
    "catalog.purchaseorder": [
        {
            title: "Order",
            aside: "supplier and dates",
            fields: [
                ["reference", 4],
                ["supplier", 4],
                ["destination_warehouse", 4],
                ["order_date", 3],
                ["expected_arrival_date", 3],
            ],
        },
        {
            title: "Lines",
            aside: "at least one",
            fields: [["lines", 12]],
        },
        {
            title: "Value and state",
            aside: "server maintained",
            fields: [
                ["total_value", 4],
                ["workflow_state_name", 4],
                ["workflow_state_code", 4],
                ["valid_transitions", 12],
            ],
        },
        {
            title: "Record",
            aside: "server maintained",
            fields: [
                ["created_at", 6],
                ["updated_at", 6],
            ],
        },
    ],
};

/** The layout for a model, or undefined to keep VUEDA's default form. */
export function getFormLayout(app, model) {
    return formLayouts[`${app}.${model}`];
}
