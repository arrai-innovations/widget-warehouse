import { useReadFallback } from "./useReadFallback.js";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { effectScope, nextTick, reactive, ref } from "vue";

const mocks = vi.hoisted(() => ({ route: vi.fn(), replace: vi.fn(), info: vi.fn() }));
vi.mock("@vueda/router/getCrud.js", () => ({ getCRUDForTo: mocks.route }));
vi.mock("vue-router", () => ({ useRouter: () => ({ replace: mocks.replace }) }));
vi.mock("@arrai-innovations/vue-sonner", () => ({ toast: { info: mocks.info } }));

const settle = async () => {
    await nextTick();
    await Promise.resolve();
    await nextTick();
};

describe("useReadFallback", () => {
    let scope;
    let props;
    let state;

    beforeEach(() => {
        vi.resetAllMocks();
        mocks.route.mockImplementation(async (target) => target);
        mocks.replace.mockResolvedValue(undefined);
        scope = effectScope();
        props = reactive({ app: "catalog", model: "purchaseorder", pk: "4" });
        state = scope.run(() => useReadFallback(props));
    });

    afterEach(() => scope.stop());

    it("waits for the emitted loading ref before replacing the update route with read", async () => {
        const loading = ref(true);
        state.object = ref({ available_actions: ["retrieve"] });
        state.loading = loading;
        await settle();
        expect(mocks.replace).not.toHaveBeenCalled();

        loading.value = false;
        await settle();
        expect(mocks.replace).toHaveBeenCalledExactlyOnceWith({
            app: "catalog",
            model: "purchaseorder",
            pk: "4",
            view: "read",
        });
        expect(mocks.info).toHaveBeenCalledOnce();
    });

    it.each([undefined, [], ["update"], ["update", "retrieve"]])(
        "does not redirect for actions %j",
        async (availableActions) => {
            state.object = { available_actions: availableActions };
            state.loading = false;
            await settle();
            expect(mocks.route).not.toHaveBeenCalled();
            expect(mocks.info).not.toHaveBeenCalled();
        },
    );

    it("observes a refreshed object that loses update permission", async () => {
        const object = ref({ available_actions: ["update", "retrieve"] });
        state.object = object;
        state.loading = false;
        await settle();
        expect(mocks.replace).not.toHaveBeenCalled();
        object.value = { available_actions: ["retrieve"] };
        await settle();
        expect(mocks.replace).toHaveBeenCalledOnce();
    });

    it("discards a pending redirect when a new fetch starts", async () => {
        let resolve;
        mocks.route.mockReturnValue(new Promise((done) => (resolve = done)));
        state.object = { available_actions: ["retrieve"] };
        state.loading = false;
        await nextTick();
        state.loading = true;
        await nextTick();
        resolve({ name: "read" });
        await settle();
        expect(mocks.replace).not.toHaveBeenCalled();
    });

    it("does not announce a redirect that navigation prevented", async () => {
        mocks.replace.mockResolvedValue(new Error("Navigation prevented"));
        state.object = { available_actions: ["retrieve"] };
        state.loading = false;
        await settle();
        expect(mocks.replace).toHaveBeenCalledOnce();
        expect(mocks.info).not.toHaveBeenCalled();
    });
});
