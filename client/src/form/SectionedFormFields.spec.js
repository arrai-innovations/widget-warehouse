import FormModel from "@vueda/form/form-model/FormModel.vue";
import { describe, expect, it, vi } from "vitest";
import { createSSRApp, h, reactive } from "vue";
import { renderToString } from "vue/server-renderer";

import SectionedFormFields from "@/form/SectionedFormFields.vue";

vi.mock("@vueda/use/useFormModel.js", () => ({
    useFormModel: () =>
        reactive({
            fields: ["name", "notes"],
            baseFieldNames: new Set(["name", "notes"]),
            fieldComponents: { name: { render: () => h("div") }, notes: { render: () => h("div") } },
            fieldProps: {},
            fieldDetails: { name: {}, notes: {} },
            widgetComponents: { name: { render: () => h("input") }, notes: { render: () => h("textarea") } },
            widgetProps: {},
        }),
}));

describe("SectionedFormFields", () => {
    it("forwards per-field slots to sectioned and unplaced fields", async () => {
        const html = await renderToString(
            createSSRApp({
                render: () =>
                    h(
                        FormModel,
                        { app: "catalog", model: "supplier" },
                        {
                            fields: ({ formModel, fieldNames }) =>
                                h(SectionedFormFields, {
                                    formModel,
                                    fieldNames,
                                    sections: [{ title: "Supplier", fields: [["name", 6]] }],
                                }),
                            "field(name)": () => h("input", { "data-field": "name" }),
                            "field(notes)": () => h("textarea", { "data-field": "notes" }),
                        },
                    ),
            }),
        );

        expect(html).toContain('data-field="name"');
        expect(html).toContain('data-field="notes"');
        expect(html).toContain('data-col="6"');
        expect(html).toContain("Unplaced");
    });
});
