/**
 * Phosphor icon registry for the VUEDA slots.
 *
 * VUEDA asks for `{ component, props }` pairs and renders them itself, so the icon library is
 * entirely the project's choice. VUEDA ships a Font Awesome Free preset
 * (`@vueda/theme/vueda-tailwind/icons/fontAwesomeFree.js`) and treats the Font Awesome packages as
 * optional peer dependencies. This file is the same registry built from a different provider, which
 * is why the project depends on no Font Awesome package at all.
 *
 * Phosphor takes its style through a `weight` prop rather than through a separate package per style,
 * so duotone is a default here instead of a different import. Sizing is left to the theme, which
 * sizes direct `svg` children.
 */
import {
    PhArrowRight,
    PhArrowSquareOut,
    PhArrowsDownUp,
    PhCalendarDots,
    PhCaretDoubleLeft,
    PhCaretDoubleRight,
    PhCaretDown,
    PhCaretLeft,
    PhCaretRight,
    PhCaretUp,
    PhCheck,
    PhCheckCircle,
    PhCircle,
    PhClock,
    PhCopy,
    PhDotsSixVertical,
    PhDotsThree,
    PhDownloadSimple,
    PhFlag,
    PhFloppyDisk,
    PhFolderOpen,
    PhFunnel,
    PhHourglassMedium,
    PhIdentificationCard,
    PhInfo,
    PhLifebuoy,
    PhList,
    PhMagnifyingGlass,
    PhMinus,
    PhPencilSimple,
    PhPlus,
    PhPrinter,
    PhProhibit,
    PhQuestion,
    PhShieldCheckered,
    PhSortAscending,
    PhSpinnerGap,
    PhTable,
    PhTrash,
    PhTray,
    PhUploadSimple,
    PhWarning,
    PhWarningCircle,
    PhX,
} from "@phosphor-icons/vue";

/**
 * Build an icon entry. Duotone is the house style, so it is the default weight; pass `weight` to
 * override it for a slot that reads better solid.
 *
 * @param {import('vue').Component} component - The Phosphor icon component.
 * @param {object} [props] - Props merged over the default weight.
 * @returns {{ component: import('vue').Component, props: object }} A VUEDA icon entry.
 */
const icon = (component, props = {}) => ({ component, props: { weight: "duotone", ...props } });

/**
 * The icon slots VUEDA renders, filled with Phosphor icons.
 *
 * @type {import('@vueda/use/useIcons.js').IconRegistry}
 */
export const phosphorIcons = {
    Checkbox: {
        check: icon(PhCheck, { weight: "bold" }),
        indeterminate: icon(PhMinus, { weight: "bold" }),
    },
    ObjectsGrid: {
        empty: icon(PhFolderOpen),
        error: icon(PhWarning),
        filtered: icon(PhQuestion),
    },
    Default: {
        actionNotFound: icon(PhProhibit),
        anglesLeft: icon(PhCaretDoubleLeft),
        anglesRight: icon(PhCaretDoubleRight),
        calendar: icon(PhCalendarDots),
        // Font Awesome splits caret and chevron across two icons. Phosphor draws one shape and
        // changes its weight, so the solid caret is the filled chevron.
        caretDown: icon(PhCaretDown, { weight: "fill" }),
        caretUp: icon(PhCaretUp, { weight: "fill" }),
        check: icon(PhCheck, { weight: "bold" }),
        chevronDown: icon(PhCaretDown, { weight: "bold" }),
        chevronLeft: icon(PhCaretLeft, { weight: "bold" }),
        chevronRight: icon(PhCaretRight, { weight: "bold" }),
        circle: icon(PhCircle),
        circleCheck: icon(PhCheckCircle),
        clock: icon(PhClock),
        close: icon(PhX, { weight: "bold" }),
        copy: icon(PhCopy),
        download: icon(PhDownloadSimple),
        ellipsis: icon(PhDotsThree, { weight: "bold" }),
        empty: icon(PhTray),
        errored: icon(PhWarningCircle),
        externalLink: icon(PhArrowSquareOut),
        filter: icon(PhFunnel),
        flag: icon(PhFlag),
        floppyDisk: icon(PhFloppyDisk),
        gripVertical: icon(PhDotsSixVertical, { weight: "bold" }),
        hourglass: icon(PhHourglassMedium),
        idCard: icon(PhIdentificationCard),
        info: icon(PhInfo),
        lifeRing: icon(PhLifebuoy),
        // Phosphor has no spin prop, so the animation is a class on the rendered svg.
        loading: icon(PhSpinnerGap, { weight: "bold", class: "animate-spin" }),
        minus: icon(PhMinus, { weight: "bold" }),
        notFound: icon(PhQuestion),
        plus: icon(PhPlus, { weight: "bold" }),
        print: icon(PhPrinter),
        rangeSeparator: icon(PhArrowRight, { weight: "bold" }),
        search: icon(PhMagnifyingGlass, { weight: "bold" }),
        shieldHalved: icon(PhShieldCheckered),
        sort: icon(PhArrowsDownUp, { weight: "bold" }),
        sortDown: icon(PhSortAscending, { weight: "bold" }),
        table: icon(PhTable),
        toggle: icon(PhList, { weight: "bold" }),
        triangleExclamation: icon(PhWarning),
        typeCreated: icon(PhPlus, { weight: "bold" }),
        typeDeleted: icon(PhTrash),
        typeUpdated: icon(PhPencilSimple),
        upload: icon(PhUploadSimple),
        warning: icon(PhWarning),
    },
};

export default phosphorIcons;
