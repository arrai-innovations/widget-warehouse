import { requireAuth, requireInitialized, requireUnauth } from "@vueda/router/guards.js";
import { makeCRUDRoutes } from "@vueda/router/makeCrud.js";
import { setCrudComponents } from "@vueda/router/routerComponent.js";
import { getPascalCaseName } from "@vueda/utils/case.js";
import { createRouter, createWebHistory } from "vue-router";

function makeViewLoader(action) {
    return async ({ app, model }) => {
        try {
            return (await import(`@/views/View${action}${getPascalCaseName(app)}${getPascalCaseName(model)}.vue`))
                .default;
        } catch {
            return (await import(`@/views/DefaultView${action}.vue`)).default;
        }
    };
}

export function getRouter(app, pinia) {
    const crudComponents = {
        list: makeViewLoader("List"),
        create: makeViewLoader("Create"),
        read: makeViewLoader("Read"),
        update: makeViewLoader("Update"),
        destroy: makeViewLoader("Destroy"),
    };
    setCrudComponents(crudComponents);

    const router = createRouter({
        history: createWebHistory(import.meta.env.BASE_URL),
        routes: [],
    });

    const routes = [
        {
            path: "/",
            name: "home",
            redirect: { name: "sign-in" },
        },
        {
            path: "/sign-in/",
            name: "sign-in",
            component: () => import("@/views/ViewSignIn.vue"),
            meta: { title: "Sign In", guest: true },
            beforeEnter: () => requireUnauth({ name: "dashboard" }, router, pinia),
        },
        {
            // The post-sign-in landing page, and the target three other places redirect
            // to. It replaced a static welcome page of hardcoded links; there is no
            // /welcome/ any more, since nothing outside this app ever linked to it.
            path: "/dashboard/",
            name: "dashboard",
            component: () => import("@/views/ViewDashboard.vue"),
            meta: { title: "Dashboard" },
            // requireAuth rather than requireInitialized. Every tile waits for a signed-in
            // user before it fetches anything, so a signed-out visitor would sit in front
            // of a page of skeletons that never resolve. This sends them to sign in and
            // adds ?redirect, which the sign-in flow prefers over its own target, so they
            // land back here.
            beforeEnter: (to) => requireAuth({ name: "sign-in" }, to, router, pinia),
        },
        ...makeCRUDRoutes({
            component: async () => (await import("@vueda/views/ViewActionRouter.vue")).default,
            authRedirect: { name: "sign-in" },
            groupsRedirect: { name: "dashboard" },
            actionRedirect: { name: "not-found" },
            groups: [],
            vueApp: app,
            router,
            pinia,
        }),
        {
            path: "/:pathMatch(.*)*",
            name: "not-found",
            component: async () => (await import("@vueda/views/ViewNotFound.vue")).default,
            meta: {
                title: "Not Found",
                titles: {
                    view: "Not Found",
                },
            },
            beforeEnter: () => requireInitialized(router, pinia),
            props: (route) => {
                return {
                    ...(route.params || {}),
                    ...(route.query || {}),
                    title: route.meta.title,
                };
            },
        },
    ];

    for (const route of routes) {
        router.addRoute(route);
    }

    return router;
}
