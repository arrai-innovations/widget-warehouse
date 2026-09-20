import { toast } from "@arrai-innovations/vue-sonner";
import { fetchHelper } from "@vueda/utils/fetchSupport.js";
import { getListUrl } from "@vueda/utils/urls.js";
import { onScopeDispose, watch } from "vue";

// Default newly selected variants without changing saved or explicitly edited prices.
export function usePurchasePriceDefaults() {
    let stop;
    onScopeDispose(() => stop?.());
    return (form) => {
        stop?.();
        const seen = new WeakMap();
        stop = watch(
            () => ({ supplier: form.state.values.supplier, lines: form.state.values.lines }),
            ({ supplier, lines }) => {
                (lines || []).forEach((line, index) => {
                    if (!line || typeof line !== "object") return;
                    const key = `${supplier}:${line.variant}`;
                    const previous = seen.get(line);
                    if (previous === key) return;
                    seen.set(line, key);
                    if (!supplier || !line.variant) return;
                    // A loaded PO line retains its recorded price. Switching its product or
                    // supplier starts a fresh lookup, while later typing invalidates the result.
                    if (
                        previous === undefined &&
                        line.unit_price !== undefined &&
                        line.unit_price !== null &&
                        line.unit_price !== ""
                    )
                        return;
                    const path = `lines.${index}.unit_price`;
                    form.updateValue(path, null);
                    const query = new URLSearchParams({ supplier, variant: line.variant, ps: 1 });
                    fetchHelper(getListUrl({ app: "catalog", model: "supplierprice", query: `?${query}` }))
                        .then((page) => {
                            const current = form.state.values.lines?.[index];
                            if (
                                current !== line ||
                                seen.get(line) !== key ||
                                `${form.state.values.supplier}:${current.variant}` !== key ||
                                current.unit_price !== null
                            )
                                return;
                            if (page.results[0]) form.updateValue(path, page.results[0].unit_cost);
                        })
                        .catch(() =>
                            toast.error(
                                "Could not load supplier cost. Enter a unit price or select the variant again.",
                            ),
                        );
                });
            },
            { deep: true, immediate: true },
        );
    };
}
