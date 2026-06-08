<script setup>
import LinkModelView from "@vueda/components/LinkModelView.vue";
import ViewList from "@vueda/views/ViewList.vue";

defineProps({
    app: { type: String, required: true },
    model: { type: String, required: true },
});
defineOptions({ inheritAttrs: false });
</script>

<template>
    <ViewList v-bind="{ ...$props, ...$attrs }">
        <!--
            Reusable per-row detail links. A model opts in by adding the matching
            synthetic column ("update" or "read") to its list displayFields (see
            src/modelConfig.js). These are not real fields, so the fetched cell is
            empty and the slot supplies a LinkModelView using the row's pk.
        -->
        <template #[`field(update)`]="{ pk }">
            <LinkModelView :app="app" :model="model" :pk="pk" view="update" label="Edit" />
        </template>
        <template #[`field(read)`]="{ pk }">
            <LinkModelView :app="app" :model="model" :pk="pk" view="read" label="View" />
        </template>
        <!-- Synthetic columns have no server-provided header; label them in card layout. -->
        <template #[`header(update)`]="slotProps">
            <div v-if="slotProps.isCardLayout" :class="slotProps.class" data-card-header="update">Actions</div>
        </template>
        <template #[`header(read)`]="slotProps">
            <div v-if="slotProps.isCardLayout" :class="slotProps.class" data-card-header="read">Actions</div>
        </template>
        <template v-for="(_, slot) in $slots" #[slot]="slotProps">
            <slot :name="slot" v-bind="slotProps || {}" />
        </template>
    </ViewList>
</template>
