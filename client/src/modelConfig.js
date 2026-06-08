import { storeModelConfig } from "@vueda/stores/storeModelConfig.js";

/**
 * Register model-level config overrides at bootstrap, before routing.
 *
 * The route guard builds and caches each model's config the first time it is
 * navigated to, so overrides must be registered before that happens. Doing it
 * here (rather than inside a view's setup) guarantees the first built config
 * already includes the override.
 *
 * @param {import('pinia').Pinia} pinia - The app's active pinia instance.
 * @returns {void}
 */
export function setupModelConfig(pinia) {
    // Showcase: add a synthetic "update" column to the widget list so each row
    // can link to its own update view. See the VUEDA guide
    // "Link List Rows to Read and Update Views". The "update" name is not a real
    // model field; it renders an empty cell that the app-wide DefaultViewList
    // fills with a LinkModelView via its reusable field(update) slot. It is
    // intentionally left out of fetchFields (nothing fetches it).
    storeModelConfig(pinia).setConfig(
        { app: "catalog", model: "widget" },
        {},
        {
            list: {
                displayFields: ["update", "name", "sku", "category", "unit_price", "is_active"],
            },
        },
    );
}
