import { DateTime } from "luxon";

// Explicit identities are part of this demo's supplier vocabulary. A filter or a new
// server ordering never changes the color or dash assigned to an existing supplier.
const supplierSlots = {
    "precision-parts-co": 0,
    "eurobearings-gmbh": 1,
    "pacific-fasteners": 2,
    "sinomech-industries": 3,
    "apex-components": 4,
};
const dashes = [[], [7, 3], [1, 3], [9, 3, 1, 3], [4, 3]];

export function supplierStyle(code) {
    // Additional suppliers get a deterministic slot. Like any five-color palette,
    // colors repeat beyond five categories; names and the data table remain explicit.
    const hash = [...code].reduce((value, char) => (value * 31 + char.charCodeAt(0)) >>> 0, 0);
    const slot = supplierSlots[code] ?? hash % 5;
    return { color: `var(--vueda-chart-${slot + 1})`, dash: dashes[slot] };
}

export function purchasingParams(weeks, today = DateTime.utc()) {
    const end = today.startOf("week");
    return {
        order_date_after: end.minus({ weeks: Number(weeks) }).toISODate(),
        order_date_before: end.minus({ days: 1 }).toISODate(),
        purchasing: "true",
    };
}

export function weekQuery(week, supplier) {
    return {
        order_date_after: week,
        order_date_before: DateTime.fromISO(week, { zone: "utc" }).plus({ days: 6 }).toISODate(),
        purchasing: "true",
        supplier,
    };
}

export function chartRows(series) {
    if (!series.length) return [];
    return series[0].values.map(({ week }, index) => ({
        week,
        timestamp: DateTime.fromISO(week, { zone: "utc" }).toMillis(),
        amounts: Object.fromEntries(series.map((supplier) => [supplier.id, supplier.values[index]?.value])),
        // Convert decimal strings only for plotting. Missing observations stay missing;
        // the server explicitly sends zero for weeks without matching order lines.
        ...Object.fromEntries(
            series.map((supplier) => [
                supplier.id,
                supplier.values[index]?.value == null ? undefined : Number(supplier.values[index].value),
            ]),
        ),
    }));
}

export const amountFormat = new Intl.NumberFormat(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
export const dateFormat = new Intl.DateTimeFormat(undefined, { day: "numeric", month: "short", timeZone: "UTC" });

// Pipeline periods include today, unlike the complete-week purchasing report.
export function pipelineParams(days, today = DateTime.utc()) {
    return days === "all"
        ? {}
        : {
              order_date_after: today.minus({ days: Number(days) - 1 }).toISODate(),
              order_date_before: today.toISODate(),
          };
}

export const weekFormat = new Intl.DateTimeFormat(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
});
