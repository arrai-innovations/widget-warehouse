import { usePurchasePriceDefaults } from "./usePurchasePriceDefaults.js";
import { describe, expect, it, vi } from "vitest";
import { effectScope, nextTick, reactive, readonly } from "vue";

const mocks = vi.hoisted(() => ({ fetch: vi.fn() }));
vi.mock("@vueda/utils/fetchSupport.js", () => ({ fetchHelper: mocks.fetch }));
vi.mock("@vueda/utils/urls.js", () => ({ getListUrl: ({ query }) => query }));
vi.mock("@arrai-innovations/vue-sonner", () => ({ toast: { error: vi.fn() } }));

function setup(values) {
    const state = reactive({ values });
    const scope = effectScope();
    const form = {
        state: readonly(state),
        updateValue(path, value) {
            const [, index, key] = path.split(".");
            state.values.lines[index][key] = value;
        },
    };
    scope.run(() => usePurchasePriceDefaults()(form));
    return { state, scope };
}

const settle = async () => {
    await nextTick();
    await Promise.resolve();
    await nextTick();
};

describe("purchase price defaults", () => {
    it("defaults a new line and preserves its explicit override", async () => {
        mocks.fetch.mockResolvedValue({ results: [{ unit_cost: "4.25" }] });
        const { state, scope } = setup({ supplier: 1, lines: [{ variant: 2 }] });
        await settle();
        expect(state.values.lines[0].unit_price).toBe("4.25");
        state.values.lines[0].unit_price = "3.00";
        await settle();
        expect(state.values.lines[0].unit_price).toBe("3.00");
        scope.stop();
    });
    it("does not reprice loaded order lines", async () => {
        mocks.fetch.mockClear();
        const { state, scope } = setup({ supplier: 1, lines: [{ id: 4, variant: 2, unit_price: "3.00" }] });
        await settle();
        expect(mocks.fetch).not.toHaveBeenCalled();
        expect(state.values.lines[0].unit_price).toBe("3.00");
        scope.stop();
    });
    it("ignores a lookup if the user typed a price while it was pending", async () => {
        let resolve;
        mocks.fetch.mockReturnValue(
            new Promise((done) => {
                resolve = done;
            }),
        );
        const { state, scope } = setup({ supplier: 1, lines: [{ variant: 2 }] });
        state.values.lines[0].unit_price = "2.99";
        resolve({ results: [{ unit_cost: "4.25" }] });
        await settle();
        expect(state.values.lines[0].unit_price).toBe("2.99");
        scope.stop();
    });
    it("discards the old supplier lookup after the supplier changes", async () => {
        let first;
        mocks.fetch
            .mockReturnValueOnce(
                new Promise((done) => {
                    first = done;
                }),
            )
            .mockResolvedValueOnce({ results: [{ unit_cost: "7.00" }] });
        const { state, scope } = setup({ supplier: 1, lines: [{ variant: 2 }] });
        state.values.supplier = 3;
        await settle();
        first({ results: [{ unit_cost: "4.25" }] });
        await settle();
        expect(state.values.lines[0].unit_price).toBe("7.00");
        scope.stop();
    });
});
