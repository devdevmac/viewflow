from django.apps import AppConfig
from django.conf.urls import url, include
from django.core.urlresolvers import reverse
from django.template import Template, TemplateDoesNotExist
from django.template.loader import get_template

from material import frontend
from material.frontend.apps import ModuleMixin

from ..compat import autodiscover_modules


class ViewflowFrontendConfig(ModuleMixin, AppConfig):
    name = 'viewflow.frontend'
    label = 'viewflow_frontend'
    verbose_name = "Workflow"
    icon = '<i class="material-icons">assignment</i>'

    def __init__(self, app_name, app_module):
        super(ViewflowFrontendConfig, self).__init__(app_name, app_module)
        self._registry = {}

    def register(self, flow_class, viewset_class=None):
        from ..flow.viewset import FlowViewSet

        if flow_class not in self._registry:
            if viewset_class is None:
                viewset_class = FlowViewSet

            self._registry[flow_class] = viewset_class(flow_class=flow_class)

    def has_perm(self, user):
        return user.is_authenticated()

    def ready(self):
        autodiscover_modules('flows', register_to=self)

    @property
    def urls(self):
        from . import views
        from viewflow.flow import views as viewflow_views

        base_url = '^workflow/'

        module_views = [
            url('^$', viewflow_views.AllTaskListView.as_view(ns_map=self.ns_map), name="index"),
            url('^queue/$', viewflow_views.AllQueueListView.as_view(ns_map=self.ns_map), name="queue"),
            url('^archive/$', viewflow_views.AllArchiveListView.as_view(ns_map=self.ns_map), name="archive"),
            url('^action/unassign/$', views.TasksUnAssignView.as_view(ns_map=self.ns_map), name="unassign"),
            url('^action/assign/$', views.TasksAssignView.as_view(ns_map=self.ns_map), name="assign"),
        ]

        for flow_class, flow_router in self._registry.items():
            flow_label = flow_class._meta.app_label
            module_views.append(
                url('^{}/'.format(flow_label), include(flow_router.urls, namespace=flow_label))
            )

        patterns = [
            url('^', (module_views, 'viewflow', 'viewflow'))
        ]

        return frontend.ModuleURLResolver(
            base_url, patterns, module=self, app_name=self.label)

    def index_url(self):
        return reverse('viewflow:index')

    def menu(self):
        try:
            return get_template('viewflow/menu.html')
        except TemplateDoesNotExist:
            return Template('')

    @property
    def ns_map(self):
        return {
            flow_class._meta.app_label: flow_class for flow_class, flow_site in self._registry.items()
        }

    @property
    def flows(self):
        return self._registry.keys()

    @property
    def sites(self):
        return sorted(
            [
                (flow_class.process_title, flow_class)
                for flow_class in self._registry.keys()
            ], key=lambda item: item[0])
