import { DateTime } from "luxon";
import { describe, expect, it } from "vitest";

import { chartRows, pipelineParams, purchasingParams, supplierStyle, weekQuery } from "@/charts/purchasing.js";

describe("charts/purchasing", () => {
    it("includes today in a thirty-day pipeline range and supports all time", () => {
        const today = DateTime.fromISO("2026-09-20", { zone: "utc" });
        expect(pipelineParams("30", today)).toEqual({
            order_date_after: "2026-08-22",
            order_date_before: "2026-09-20",
        });
        expect(pipelineParams("all", today)).toEqual({});
    });
    it("requests complete UTC weeks and gives drill-down links the same state/date filters", () => {
        const params = purchasingParams(6, DateTime.fromISO("2026-09-20T23:30:00Z", { zone: "utc" }));
        expect(params).toEqual({ order_date_after: "2026-08-03", order_date_before: "2026-09-13", purchasing: "true" });
        expect(weekQuery(params.order_date_after, "supplier-id")).toEqual({
            order_date_after: "2026-08-03",
            order_date_before: "2026-08-09",
            purchasing: "true",
            supplier: "supplier-id",
        });
    });
    it("does not reassign colors or dashes when supplier order or membership changes", () => {
        const codes = [
            "precision-parts-co",
            "eurobearings-gmbh",
            "pacific-fasteners",
            "sinomech-industries",
            "apex-components",
        ];
        const styles = Object.fromEntries(codes.map((code) => [code, supplierStyle(code)]));
        for (const code of codes.slice(1).reverse()) expect(supplierStyle(code)).toEqual(styles[code]);
        expect(new Set(Object.values(styles).map((style) => style.color)).size).toBe(5);
        expect(new Set(Object.values(styles).map((style) => style.dash.join())).size).toBe(5);
    });
    it("preserves managed rows and distinguishes zero from missing observations", () => {
        const series = Object.freeze([
            Object.freeze({
                id: "one",
                values: Object.freeze([
                    { week: "2026-08-03", value: "0.00" },
                    { week: "2026-08-10", value: "12.34" },
                ]),
            }),
            Object.freeze({
                id: "two",
                values: Object.freeze([
                    { week: "2026-08-03", value: "5.00" },
                    { week: "2026-08-10", value: null },
                ]),
            }),
        ]);
        const rows = chartRows(series);
        expect(rows[0].one).toBe(0);
        expect(rows[1].one).toBe(12.34);
        expect(rows[1].two).toBeUndefined();
        expect(series[0].values[1].value).toBe("12.34");
    });
});
