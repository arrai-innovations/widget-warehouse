<script setup>
import LinkModelView from "@vueda/navigation/link-model-view/LinkModelView.vue";

import DefaultViewList from "@/views/DefaultViewList.vue";

// Model-specific list for catalog.widget. Wraps the app-wide DefaultViewList so
// it inherits the reusable per-row links, then adds a model-specific touch:
// the existing "name" column links to the widget's read view. This keeps the
// "link an existing column" alternative alongside the synthetic "update" (Edit)
// column that DefaultViewList adds for update-capable models.
defineProps({
    app: { type: String, required: true },
    model: { type: String, required: true },
});
defineOptions({ inheritAttrs: false });
</script>

<template>
    <DefaultViewList v-bind="{ ...$props, ...$attrs }">
        <template #[`field(name)`]="{ pk, formatted }">
            <LinkModelView :app="app" :model="model" :pk="pk" view="read">
                {{ formatted }}
            </LinkModelView>
        </template>
        <template v-for="(_, slot) in $slots" #[slot]="slotProps">
            <slot :name="slot" v-bind="slotProps || {}" />
        </template>
    </DefaultViewList>
</template>
