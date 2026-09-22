<script setup>
import FieldRenderer from "@vueda/form/form-model/FieldRenderer.vue";
import FormGrid from "@vueda/form/layout/FormGrid.vue";
import FormSection from "@vueda/form/layout/FormSection.vue";
import FormSectionTitle from "@vueda/form/layout/FormSectionTitle.vue";
import { computed } from "vue";

/**
 * Sectioned, multi-column field layout for create and update forms, driven by a layout
 * from `formLayouts.js`.
 *
 * VUEDA's default form is one full-width field per row, which is the right default for a
 * model whose field list is unknown but a poor fit once it is known: short fields such as
 * codes, dates, and flags waste a row each, an inline or a long text field wants the whole
 * width, and read-only server-maintained values should not compete with the fields an
 * operator fills in.
 *
 * This is the composition path for that: `FormModel` exposes a `fields` slot that replaces
 * its default loop, and `FormSection` and `FormGrid` are the layout primitives meant to go
 * inside it. Spans are expressed as `data-col`, not as `col-span-*` classes, so the grid's
 * breakpoint and gaps stay in `FormGrid`'s theme entry and a re-skin can retarget every
 * form at once.
 *
 * Two shapes here are forced by the current VUEDA surface rather than chosen:
 *
 * - `FieldRenderer` spreads its own attributes into both the field and the widget, and
 *   `FormField` forwards only `class` onto the field wrapper, so a `data-col` set on a
 *   `FieldRenderer` lands on the input instead of the grid child. Each field is therefore
 *   wrapped in a plain `div` that carries the span.
 * - Anything not named in the layout would silently vanish from the form, so the trailing
 *   section renders whatever the model gained since its layout was written. It exists so a
 *   new server field shows up somewhere instead of nowhere.
 */
defineOptions({
    // The `fields` slot binds the whole form-model context; none of it belongs on the DOM.
    inheritAttrs: false,
});

const props = defineProps({
    /** Form model context from `FormModel`'s `fields` slot. */
    formModel: {
        type: Object,
        required: true,
    },
    /** Non-expanded field names the form is rendering, from the same slot. */
    fieldNames: {
        type: [Array, Set],
        required: true,
    },
    /** Ordered sections of `{ title, aside, fields: [[name, columns], ...] }`. */
    sections: {
        type: Array,
        required: true,
    },
});

const renderedFieldNames = computed(() => new Set(props.fieldNames));

// A section drops out entirely when config leaves none of its fields in the form, so a
// narrowed displayFields list does not leave a heading standing over nothing.
const visibleSections = computed(() =>
    props.sections
        .map((section) => ({
            ...section,
            fields: section.fields.filter(([name]) => renderedFieldNames.value.has(name)),
        }))
        .filter((section) => section.fields.length),
);

const placedFieldNames = computed(
    () => new Set(props.sections.flatMap((section) => section.fields.map(([name]) => name))),
);

const unplacedFields = computed(() =>
    [...renderedFieldNames.value].filter((name) => !placedFieldNames.value.has(name)),
);
</script>

<template>
    <FormSection v-for="section in visibleSections" :key="section.title">
        <template #title>
            <FormSectionTitle>{{ section.title }}</FormSectionTitle>
        </template>
        <template v-if="section.aside" #aside>{{ section.aside }}</template>
        <FormGrid>
            <div v-for="[name, columns] in section.fields" :key="name" :data-col="columns">
                <FieldRenderer :form-model="formModel" :form-model-name="name" />
            </div>
        </FormGrid>
    </FormSection>
    <FormSection v-if="unplacedFields.length">
        <template #title>
            <FormSectionTitle>Unplaced</FormSectionTitle>
        </template>
        <template #aside>not yet assigned a section</template>
        <FormGrid>
            <div v-for="name in unplacedFields" :key="name">
                <FieldRenderer :form-model="formModel" :form-model-name="name" />
            </div>
        </FormGrid>
    </FormSection>
</template>
