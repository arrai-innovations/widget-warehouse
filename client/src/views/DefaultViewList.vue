<script setup>
import ErrorDisplay from "@vueda/components/ErrorDisplay.vue";
import FilterGroup from "@vueda/components/FilterGroup.vue";
import LinkModelView from "@vueda/components/LinkModelView.vue";
import LoadingSpinnerInline from "@vueda/components/LoadingSpinnerInline.vue";
import MobileSortComponent from "@vueda/components/MobileSortComponent.vue";
import ObjectsGrid from "@vueda/components/ObjectsGrid.vue";
import ObjectsGridBodyCell from "@vueda/components/ObjectsGridBodyCell.vue";
import PaginationComponent from "@vueda/components/PaginationComponent.vue";
import StickyBar from "@vueda/components/StickyBar.vue";
import Checkbox from "@vueda/controls/checkbox/Checkbox.vue";
import InputGroup from "@vueda/controls/input-group/InputGroup.vue";
import InputGroupButton from "@vueda/controls/input-group/InputGroupButton.vue";
import InputGroupInput from "@vueda/controls/input-group/InputGroupInput.vue";
import Select from "@vueda/controls/select/Select.vue";
import SelectContent from "@vueda/controls/select/SelectContent.vue";
import SelectItem from "@vueda/controls/select/SelectItem.vue";
import SelectTrigger from "@vueda/controls/select/SelectTrigger.vue";
import SelectValue from "@vueda/controls/select/SelectValue.vue";
import { useSlotNameResolver } from "@vueda/use/useSlotNameResolver.js";
import { useViewList } from "@vueda/use/useViewList.js";
import { getCRUDName, memoizedStartCase } from "@vueda/utils/case.js";
import omit from "lodash-es/omit.js";
import { useSlots } from "vue";

defineOptions({
    inheritAttrs: false,
});
const props = defineProps({
    app: {
        type: String,
        required: true,
    },
    model: {
        type: String,
        required: true,
    },
    listFields: {
        type: Array,
        default: () => [],
    },
    displayFields: {
        type: Object,
        default: () => ({}),
    },
    relatedObjectsRules: {
        type: Object,
        default: () => ({}),
    },
    calculatedObjectsRules: {
        type: Object,
        default: () => ({}),
    },
    params: {
        type: Object,
        default: () => ({}),
    },
    tableBreakpoint: {
        type: String,
        default: "lg",
    },
    extraFieldObjects: {
        type: Array,
        default: () => [
            {
                name: `selected_`,
                extra: true,
                label: "Selected",
            },
        ],
    },
    filterables: {
        type: Array,
        default: undefined,
    },
    filterableDetails: {
        type: Object,
        default: () => ({}),
    },
    allowShowAllPages: {
        type: Boolean,
        default: true,
    },
    alwaysShowAllPages: {
        type: Boolean,
        default: false,
    },
    showTotalRecordNum: {
        type: Boolean,
        default: true,
    },
    allowColumnHiding: {
        type: Boolean,
        default: false,
    },
});

const { modelConfig, list, actions, search, sort, columns, pagination } = useViewList(props);

const slots = useSlots();
const targetlessActionButtonSlotName = useSlotNameResolver(["targetless-action-button", "button"]);
const bulkActionButtonSlotName = useSlotNameResolver(["bulk-action-button", "button"]);
const workflowActionButtonSlotName = useSlotNameResolver(["workflow-action-button", "button"]);
</script>
<template>
    <div>
        <div>
            <div>
                <div>
                    <div>
                        <h1>
                            <slot name="title">{{ list.titleStr }}</slot>
                            <template v-if="list.instanceList.state.loading">
                                &nbsp;
                                <loading-spinner-inline />
                            </template>
                        </h1>
                        <slot name="title-suffix" />
                    </div>
                    <div>
                        <slot name="targetless-action-buttons" :targetless-actions="actions.targetlessActions">
                            <template
                                v-for="actionName in actions.targetlessActions"
                                :key="getCRUDName({ app: app, model: model, view: actionName })"
                            >
                                <slot
                                    :name="targetlessActionButtonSlotName.name"
                                    v-bind="actions.buttonSlotProps[actionName]"
                                >
                                    <link-model-view v-bind="actions.buttonSlotProps[actionName]" />
                                </slot>
                            </template>
                        </slot>
                    </div>
                    <hr />
                </div>
                <hr />
                <div>
                    <div data-qa="view-list-under-actions">
                        <div data-qa="view-list-action-buttons">
                            <template v-for="actionName in actions.bulkActions" :key="actionName">
                                <slot
                                    :name="bulkActionButtonSlotName.name"
                                    v-bind="actions.buttonSlotProps[actionName]"
                                >
                                    <link-model-view
                                        button
                                        :pk="actions.buttonSlotProps[actionName].selectedObjects"
                                        v-bind="omit(actions.buttonSlotProps[actionName], ['selectedObjects'])"
                                        class="grow sm:grow-0"
                                    />
                                </slot>
                            </template>
                            <template v-for="actionName in actions.availableTransitions" :key="actionName">
                                <slot
                                    :name="workflowActionButtonSlotName.name"
                                    v-bind="actions.buttonSlotProps[actionName]"
                                >
                                    <link-model-view
                                        button
                                        :pk="actions.buttonSlotProps[actionName].selectedObjects"
                                        v-bind="omit(actions.buttonSlotProps[actionName], ['selectedObjects'])"
                                        class="grow sm:grow-0"
                                    />
                                </slot>
                            </template>
                        </div>
                        <div>
                            <slot name="search" v-bind="search.searchSlotProps">
                                <InputGroup>
                                    <InputGroupInput
                                        class="lg:max-w-[30ch]"
                                        :model-value="search.searchSlotProps.listSearch"
                                        name="search"
                                        placeholder="Search"
                                        type="search"
                                        @search="search.filterList"
                                        @update:model-value="search.searchSlotProps.updateListSearch"
                                    />
                                    <InputGroupButton @click="search.filterList"> Search </InputGroupButton>
                                </InputGroup>
                            </slot>
                            <slot
                                v-if="modelConfig.config?.allowColumnHiding || allowColumnHiding"
                                name="columns-select"
                                :columns="columns.columns"
                                :options="columns.columnOptions"
                                :loading="list.loading"
                            >
                                <Select v-model="columns.columns" multiple>
                                    <SelectTrigger size="sm">
                                        <SelectValue>
                                            <slot name="columns-select-value-label">columns</slot>
                                        </SelectValue>
                                        <template v-if="slots['columns-select-dropdown-icon']" #icon>
                                            <slot name="columns-select-dropdown-icon" />
                                        </template>
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem
                                            v-for="option in columns.columnOptions"
                                            :key="option.value"
                                            :value="option.value"
                                        >
                                            {{ option.label }}
                                        </SelectItem>
                                    </SelectContent>
                                </Select>
                            </slot>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <sticky-bar class="w-full">
            <filter-group
                v-model="list.listState.filterArgs"
                :app="props.app"
                :model="props.model"
                :view="'list'"
                :error="list.instanceList.state.error"
                :errored="list.instanceList.state.errored"
                :filterable-details="props.filterableDetails"
                :filterables="props.filterables"
            >
                <template v-for="(_, slot) in slots" #[slot]="slotProps">
                    <slot :name="slot" v-bind="slotProps || {}" />
                </template>
            </filter-group>
            <div class="flex flex-row justify-end">
                <mobile-sort-component
                    v-if="sort.canShowMobileSorter"
                    v-model:visible="sort.mobileSortDrawerVisible"
                    :header="`Sort ${memoizedStartCase(modelConfig.config?.verboseNamePlural || 'items')}`"
                    :field-details="modelConfig.config?.fieldDetails || {}"
                    :sortables="sort.sortablesList"
                    :sorted="sort.sorting.state.sorted"
                    @update:sorted="sort.sorting.updateSorted"
                >
                    <template v-for="(_, slot) in slots" #[slot]="slotProps">
                        <slot :name="slot" v-bind="slotProps || {}" />
                    </template>
                </mobile-sort-component>
            </div>
        </sticky-bar>

        <slot name="additional-errors" />
        <error-display :error="list.error" :errored="list.errored" @dismiss-error="list.dismissError" />
        <slot name="before-list" />
        <objects-grid
            v-bind="$attrs"
            :calculated-objects="list.instanceList.state.calculatedObjects"
            class="w-full"
            :field-classes="{
                ...($attrs.fieldClasses || {}),
                selected_: 'lg:w-0',
            }"
            :field-props="{
                pkKey: modelConfig.info?.pk ?? 'id',
                modelInfo: modelConfig.info,
                modelConfig: modelConfig.config,
            }"
            :fields="list.computedFieldObjects"
            :loading="list.loading"
            :objects-in-order="list.instanceList.state.objectsInOrder"
            :related-objects="list.instanceList.state.relatedObjects"
            :sortables="sort.sorting.state.sortables"
            :sorted="sort.sorting.state.sorted"
            :table-breakpoint="tableBreakpoint"
            @update:sorted="sort.sorting.updateSorted"
            @update:is-table="sort.isTable = $event"
        >
            <template
                v-for="slot in Object.keys(slots).filter((slot) => !list.specialSlots.includes(slot))"
                #[slot]="slotProps"
            >
                <slot :name="slot" v-bind="slotProps || {}"></slot>
            </template>
            <template v-for="field in extraFieldObjects" :key="field.name" #[`header(${field.name})`]="slotProps">
                <slot :name="`field(${field.name})`" v-bind="slotProps">
                    <div :class="slotProps.class" :data-card-header="field.name">
                        {{ slotProps.girdType === "cell" ? field.label : "" }}
                    </div>
                </slot>
            </template>
            <template v-for="field in extraFieldObjects" :key="field.name" #[`field(${field.name})`]="slotProps">
                <slot
                    v-bind="slotProps"
                    :has-selectable-actions="actions.bulkActions.size || actions.availableTransitions.size"
                    :name="`field(${field.name})`"
                >
                    <Checkbox
                        v-if="actions.bulkActions.size || actions.availableTransitions.size"
                        :id="`selected-row-${slotProps.pk}`"
                        :model-value="actions.selectedObjects.includes(slotProps.pk)"
                        name="selected"
                        v-bind="slotProps"
                        @update:model-value="actions.toggleSelectedObject(slotProps.pk)"
                    />
                </slot>
            </template>
            <template #row-after-objects="slotProps">
                <slot name="row-after-objects" v-bind="slotProps" :column-totals="list.columnTotals">
                    <div
                        v-if="sort.isTable && Object.keys(list.columnTotals).length"
                        :class="slotProps.class"
                        role="row"
                    >
                        <objects-grid-body-cell
                            v-for="(field, index) in list.computedFieldObjects"
                            :key="field.name"
                            :field="field"
                            :obj="{}"
                            :related-object="{}"
                            :calculated-object="{}"
                            :row-index="0"
                            :column-index="index"
                            :row-count="1"
                            :column-count="list.computedFieldObjects.length"
                            :pk-key="list.pkKey"
                            class="border-t-2"
                        >
                            <template #value>
                                <slot :name="`field(${field.name})totals`" :value="list.columnTotals[field.name]">
                                    {{ list.columnTotals[field.name] ?? "" }}
                                </slot>
                            </template>
                        </objects-grid-body-cell>
                    </div>
                </slot>
            </template>
        </objects-grid>
        <pagination-component
            v-if="pagination.paginateInfo?.totalRecords > 0"
            v-model:current-page="list.listState.currentPage"
            :loading="list.instanceList.state.loading"
            :rows="pagination.paginateInfo?.perPage"
            :total-records="pagination.paginateInfo?.totalRecords"
            :is-table="sort.isTable"
            :showing-all-pages="pagination.computedShowAllPages"
            :allow-show-all-pages="modelConfig.config?.allowShowAllPages && allowShowAllPages"
            :show-total-record-num="modelConfig.config?.showTotalRecordNum && showTotalRecordNum"
            @update:showing-all-pages="pagination.showingAllPages = $event"
        >
            <template v-for="(_, slot) in slots" #[slot]="slotProps">
                <slot :name="slot" v-bind="slotProps || {}" />
            </template>
        </pagination-component>
    </div>
</template>
