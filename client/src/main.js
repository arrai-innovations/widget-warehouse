import TheApp from "./TheApp.vue";
import { getRouter } from "./router/index.js";
import { config as faConfig } from "@fortawesome/fontawesome-svg-core";
import "@fortawesome/fontawesome-svg-core/styles.css";
import {
    faAnglesLeft,
    faAnglesRight,
    faArrowRightLong,
    faBan,
    faBars,
    faCaretDown,
    faCaretUp,
    faCheck,
    faChevronDown,
    faChevronLeft,
    faChevronRight,
    faCircle,
    faCircleCheck,
    faCircleExclamation,
    faCircleInfo,
    faCircleQuestion,
    faClock,
    faCopy,
    faDownload,
    faEllipsis,
    faFilter,
    faFlag,
    faFloppyDisk,
    faFolderOpen,
    faGripVertical,
    faInbox,
    faLifeRing,
    faMinus,
    faPlus,
    faPrint,
    faSort,
    faSortDown,
    faSpinner,
    faTriangleExclamation,
    faXmark,
} from "@fortawesome/sharp-duotone-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import vuedaTailwind from "@vueda/theme/vueda-tailwind/index.js";
import { setIcons } from "@vueda/use/useIcons.js";
import { setTheme } from "@vueda/use/useTheme.js";
import { setupDefaultListCrud } from "@vueda/utils/listCrud.js";
import { setupDefaultObjectCrud } from "@vueda/utils/objectCrud.js";
import { createPinia } from "pinia";
import { createApp } from "vue";

import { setupModelConfig } from "@/setupModelConfig.js";

faConfig.autoAddCss = false;

setTheme(vuedaTailwind);
setIcons({
    Checkbox: {
        check: { component: FontAwesomeIcon, props: { icon: faCheck } },
        indeterminate: { component: FontAwesomeIcon, props: { icon: faMinus } },
    },
    ObjectsGrid: {
        empty: { component: FontAwesomeIcon, props: { icon: faFolderOpen } },
        error: { component: FontAwesomeIcon, props: { icon: faTriangleExclamation } },
        filtered: { component: FontAwesomeIcon, props: { icon: faCircleQuestion } },
    },
    Default: {
        actionNotFound: { component: FontAwesomeIcon, props: { icon: faBan } },
        anglesLeft: { component: FontAwesomeIcon, props: { icon: faAnglesLeft } },
        anglesRight: { component: FontAwesomeIcon, props: { icon: faAnglesRight } },
        caretDown: { component: FontAwesomeIcon, props: { icon: faCaretDown } },
        caretUp: { component: FontAwesomeIcon, props: { icon: faCaretUp } },
        check: { component: FontAwesomeIcon, props: { icon: faCheck } },
        chevronDown: { component: FontAwesomeIcon, props: { icon: faChevronDown } },
        chevronLeft: { component: FontAwesomeIcon, props: { icon: faChevronLeft } },
        chevronRight: { component: FontAwesomeIcon, props: { icon: faChevronRight } },
        circle: { component: FontAwesomeIcon, props: { icon: faCircle } },
        circleCheck: { component: FontAwesomeIcon, props: { icon: faCircleCheck } },
        clock: { component: FontAwesomeIcon, props: { icon: faClock } },
        close: { component: FontAwesomeIcon, props: { icon: faXmark } },
        copy: { component: FontAwesomeIcon, props: { icon: faCopy } },
        download: { component: FontAwesomeIcon, props: { icon: faDownload } },
        ellipsis: { component: FontAwesomeIcon, props: { icon: faEllipsis } },
        empty: { component: FontAwesomeIcon, props: { icon: faInbox } },
        errored: { component: FontAwesomeIcon, props: { icon: faCircleExclamation } },
        filter: { component: FontAwesomeIcon, props: { icon: faFilter } },
        flag: { component: FontAwesomeIcon, props: { icon: faFlag } },
        floppyDisk: { component: FontAwesomeIcon, props: { icon: faFloppyDisk } },
        gripVertical: { component: FontAwesomeIcon, props: { icon: faGripVertical } },
        info: { component: FontAwesomeIcon, props: { icon: faCircleInfo } },
        lifeRing: { component: FontAwesomeIcon, props: { icon: faLifeRing } },
        loading: { component: FontAwesomeIcon, props: { icon: faSpinner, spin: true } },
        notFound: { component: FontAwesomeIcon, props: { icon: faCircleQuestion } },
        plus: { component: FontAwesomeIcon, props: { icon: faPlus } },
        print: { component: FontAwesomeIcon, props: { icon: faPrint } },
        rangeSeparator: { component: FontAwesomeIcon, props: { icon: faArrowRightLong } },
        sort: { component: FontAwesomeIcon, props: { icon: faSort } },
        sortDown: { component: FontAwesomeIcon, props: { icon: faSortDown } },
        toggle: { component: FontAwesomeIcon, props: { icon: faBars } },
        triangleExclamation: { component: FontAwesomeIcon, props: { icon: faTriangleExclamation } },
        warning: { component: FontAwesomeIcon, props: { icon: faTriangleExclamation } },
    },
});
setupDefaultListCrud();
setupDefaultObjectCrud();

const app = createApp(TheApp);
const pinia = createPinia();

app.use(pinia);
setupModelConfig(pinia);

const router = getRouter(app, pinia);

app.use(router);

app.mount("#the-app");

export default app;
