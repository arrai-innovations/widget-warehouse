<script setup>
import ErrorDisplay from "@vueda/components/ErrorDisplay.vue";
import FormModel from "@vueda/components/FormModel.vue";
import LinkModelView from "@vueda/components/LinkModelView.vue";
import LoadingSpinnerInline from "@vueda/components/LoadingSpinnerInline.vue";
import PageActions from "@vueda/components/PageActions.vue";
import StickyBar from "@vueda/components/StickyBar.vue";
import Button from "@vueda/controls/button/Button.vue";
import { usePageTitle } from "@vueda/use/usePageTitle.js";
import { useViewUpdate } from "@vueda/use/useViewUpdate.js";
import { memoizedStartCase } from "@vueda/utils/case.js";
import { FormContextSymbol } from "@vueda/utils/symbols.js";
import { onMounted, provide, readonly, toRef, useSlots } from "vue";

defineOptions({ inheritAttrs: false });

const props = defineProps({
    app: { type: String, required: true },
    model: { type: String, required: true },
    pk: { type: String, required: true },
    submitFields: { type: Array, default: undefined },
    redirectAfter: {
        type: String,
        default: null,
        validator: (value) => ["list", "read", null].includes(value),
    },
    class: { type: [String, Array, Object], default: () => [] },
    outerClass: { type: [String, Array, Object], default: () => [] },
    formModelVariant: { type: String, default: "default" },
    fields: { type: Array, default: undefined },
    fieldDetails: { type: Object, default: undefined },
    expand: { type: Array, default: undefined },
    expandDetails: { type: Object, default: undefined },
    fieldComponents: { type: Object, default: undefined },
    widgetComponents: { type: Object, default: undefined },
    formProps: { type: Object, default: undefined },
    fieldProps: { type: Object, default: undefined },
    widgetProps: { type: Object, default: undefined },
    relatedObjectRules: { type: Object, default: () => ({}) },
    calculatedObjectRules: { type: Object, default: () => ({}) },
    fetchFields: { type: Array, default: undefined },
});

const emit = defineEmits(["object", "loading", "related-object", "calculated-object", "form-object", "form-context"]);

const slots = useSlots();

const { formContext, objectForm, instanceObject, instance, actions } = useViewUpdate(props);

// Contribute the page title and loading state to the layout's ThePageTitle display.
usePageTitle(() => ({ title: instance.titleStr, loading: instance.pageLoading }));

provide(FormContextSymbol, formContext);

onMounted(() => {
    emit(
        "object",
        toRef(() => instanceObject.state.object),
    );
    emit(
        "loading",
        toRef(() => instanceObject.state.loading),
    );
    emit("related-object", readonly(instanceObject.state.relatedObjects || {}));
    emit("calculated-object", readonly(instanceObject.state.calculatedObjects || {}));
    emit(
        "form-object",
        toRef(() => formContext.state.values),
    );
    emit("form-context", formContext);
});
</script>
<template>
    <div :class="props.class" data-qa="update-form-root">
        <!-- Page-level actions teleport into the layout's ThePageTitle action zone. -->
        <page-actions>
            <template v-for="actionName in actions.nonDetailActions" :key="actionName">
                <slot
                    :app="app"
                    :label="memoizedStartCase(actionName)"
                    :model="model"
                    name="targetless-action-button"
                    :view="actionName"
                >
                    <link-model-view
                        :app="app"
                        :label="memoizedStartCase(actionName)"
                        :model="model"
                        :view="actionName"
                    />
                </slot>
            </template>
            <slot name="extra-buttons" />
        </page-actions>
        <sticky-bar class="w-full">
            <div data-qa="update-action-button">
                <slot
                    :form="instance.formId"
                    label="Submit"
                    :loading="objectForm.state.loading"
                    :modified="formContext.state.anyModified"
                    name="submit-button"
                    type="submit"
                >
                    <Button :form="instance.formId" :disabled="objectForm.state.loading" type="submit">
                        <LoadingSpinnerInline v-if="objectForm.state.loading" />
                        Submit
                    </Button>
                </slot>
                <template v-for="actionName in actions.detailActions" :key="actionName">
                    <slot
                        :app="app"
                        :label="memoizedStartCase(actionName)"
                        :model="model"
                        name="action-button"
                        :pk="pk"
                        :view="actionName"
                    >
                        <link-model-view
                            :app="app"
                            button
                            :label="memoizedStartCase(actionName)"
                            :model="model"
                            :pk="pk"
                            severity="secondary"
                            :view="actionName"
                        />
                    </slot>
                </template>
                <template v-for="transition in actions.availableTransitions" :key="transition">
                    <slot
                        :app="app"
                        :label="memoizedStartCase(transition)"
                        :model="model"
                        name="transition-button"
                        :pk="pk"
                        :view="transition"
                    >
                        <link-model-view
                            :app="app"
                            button
                            :label="memoizedStartCase(transition)"
                            :model="model"
                            :pk="pk"
                            severity="secondary"
                            :view="transition"
                        />
                    </slot>
                </template>
            </div>
        </sticky-bar>
        <div :class="props.outerClass" data-qa="update-form">
            <error-display
                :error="instance.combinedError"
                :errored="instance.combinedErrored"
                :ignore-form-validation-errors="true"
                :while-text="instance.combinedWhileText"
            />
            <form v-bind="$attrs" :id="instance.formId" @submit.prevent="objectForm.submit">
                <form-model
                    :app="app"
                    :field-components="fieldComponents"
                    :field-details="fieldDetails"
                    :field-props="fieldProps"
                    :fields="fields"
                    :expand="expand"
                    :expand-details="expandDetails"
                    :model="model"
                    :variant="formModelVariant"
                    view="update"
                    :widget-components="widgetComponents"
                    :widget-props="instance.computedWidgetProps"
                    v-bind="instance.combinedFormProps"
                >
                    <template v-for="(_, slot) in slots" #[slot]="slotProps">
                        <slot :name="slot" v-bind="slotProps || {}" />
                    </template>
                </form-model>
            </form>
        </div>
    </div>
</template>
