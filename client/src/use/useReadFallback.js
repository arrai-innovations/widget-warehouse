import { toast } from "@arrai-innovations/vue-sonner";
import { getCRUDForTo } from "@vueda/router/getCrud.js";
import { reactive, watch } from "vue";
import { useRouter } from "vue-router";

// ViewUpdate emits live object/loading refs. Reactive state unwraps them so a
// later fetch can also move an order that is no longer editable to its read view.
export function useReadFallback(props) {
    const router = useRouter();
    const state = reactive({ object: null, loading: true });

    watch(
        () => [state.object?.available_actions, state.loading, props.app, props.model, props.pk],
        async ([actions, loading, app, model, pk], _, onCleanup) => {
            if (loading !== false || !actions || actions.includes("update") || !actions.includes("retrieve")) {
                return;
            }
            let cancelled = false;
            onCleanup(() => {
                cancelled = true;
            });
            const route = await getCRUDForTo({ app, model, pk, view: "read" });
            if (cancelled) {
                return;
            }
            const failure = await router.replace(route);
            if (!failure) {
                toast.info("Showing the read view because this record is currently unavailable for editing.");
            }
        },
    );

    return state;
}
