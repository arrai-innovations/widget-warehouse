import { requireInitialized, requireUnauth } from "@vueda/router/guards.js";
import { makeCRUDRoutes } from "@vueda/router/makeCrud.js";
import { setCrudComponents } from "@vueda/router/routerComponent.js";
import { createRouter, createWebHistory } from "vue-router";

export function getRouter(app, pinia) {
    const crudComponents = {
        list: async () => (await import("@vueda/views/ViewList.vue")).default,
        create: async () =>
            (await import("@vueda/views/ViewCreate.vue")).default,
        read: async () => (await import("@vueda/views/ViewRead.vue")).default,
        update: async () =>
            (await import("@vueda/views/ViewUpdate.vue")).default,
        destroy: async () =>
            (await import("@vueda/views/ViewDestroy.vue")).default,
    };
    setCrudComponents(crudComponents);

    const router = createRouter({
        history: createWebHistory(import.meta.env.BASE_URL),
        routes: [],
    });

    const routes = [
        {
            path: "/",
            name: "landing",
            component: () => import("@/views/ViewLanding.vue"),
            meta: { title: "Landing" },
            beforeEnter: () => requireUnauth({ name: 'welcome' }, router, pinia)
        },
        {
            path: "/sign-in/",
            name: "sign-in",
            component: () => import("@/views/ViewSignIn.vue"),
            meta: { title: "Sign In" },
            beforeEnter: () => requireUnauth({ name: 'welcome' }, router, pinia)
        },
        {
            path: "/welcome/",
            name: "welcome",
            component: () => import("@/views/ViewWelcome.vue"),
            meta: { title: "Welcome" },
            beforeEnter: () => requireInitialized(router, pinia),
        },
        ...makeCRUDRoutes({
            component: async () =>
                (await import("@vueda/views/ViewActionRouter.vue")).default,
            authRedirect: { name: "sign-in" },
            groupsRedirect: { name: "welcome" },
            actionRedirect: { name: "not-found" },
            groups: [],
            vueApp: app,
            router,
            pinia,
        }),
        {
            path: "/:pathMatch(.*)*",
            name: "not-found",
            component: async () =>
                (await import("@vueda/views/ViewNotFound.vue")).default,
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
