from .utils import LinkNotFoundError
from bs4 import BeautifulSoup


class Form(object):

    def __init__(self, form):
        self.form = form

    def input(self, data):
        """Fill-in a set of fields in a form.

        Example: filling-in a login/password form

        .. code-block:: python

           form.input({"login": username, "password": password})

        This will find the input element named "login" and give it the
        value ``username``, and the input element named "password" and
        give it the value ``password``.

        The type of element (input, textarea, select, ...) does not
        need to be given.
        """

        for (name, value) in data.items():
            i = self.form.find("input", {"name": name})
            if not i:
                raise LinkNotFoundError("No input field named " + name)
            i["value"] = value

    attach = input

    def uncheck_all(self, name):
        for option in self.form.find_all("input", {"name": name}):
            if "checked" in option.attrs:
                del option.attrs["checked"]

    def check(self, data):
        for (name, value) in data.items():
            # Complain if we don't find the name, regardless of the value
            inputs = self.form.find_all("input", {"name": name})
            if inputs == []:
                raise LinkNotFoundError("No input checkbox named " + name)

            # We assume that all inputs with this name have the same type
            if inputs[0].attrs.get('type', 'text') not in ("radio",
                                                           "checkbox"):
                raise LinkNotFoundError("Types must be radio or checkbox")

            # For radio buttons, only one may be checked
            # (Not so for checkboxes, but assume only specified are desired)
            self.uncheck_all(name)

            # Accept individual values (int, str)
            # We just wrap them in a 1-value tuple.
            if not isinstance(value, list) and not isinstance(value, tuple):
                value = (value,)
            for choice in value:
                choice_str = str(choice)  # Allow for example literal numbers
                for i in inputs:
                    if i.attrs.get("value", "on") == choice_str or choice is True:
                        i["checked"] = ""
                        break
                else:
                    print(self.form)
                    # TODO: this should not be excepted
                    raise LinkNotFoundError(
                        "No input checkbox named %s with choice %s" %
                        (name, choice)
                    )

    def textarea(self, data):
        for (name, value) in data.items():
            t = self.form.find("textarea", {"name": name})
            if not t:
                raise LinkNotFoundError("No textarea named " + name)
            t.string = value

    def select(self, data):
        for (name, value) in data.items():
            select = self.form.find("select", {"name": name})
            if not select:
                raise LinkNotFoundError("No select named " + name)
            for option in select.find_all("option"):
                if "selected" in option.attrs:
                    del option.attrs["selected"]
            o = select.find("option", {"value": value})
            o.attrs["selected"] = "selected"

    def __setitem__(self, name, value):
        return self.set(name, value)

    def set(self, name, value, force=False):
        try:
            self.check({name: value})
            return
        except LinkNotFoundError:
            pass
        try:
            self.input({name: value})
            return
        except LinkNotFoundError:
            pass
        try:
            self.textarea({name: value})
            return
        except LinkNotFoundError:
            pass
        try:
            self.select({name: value})
            return
        except LinkNotFoundError:
            pass
        if force:
            self.new_control('input', name, value=value)
            return
        raise LinkNotFoundError()

    def new_control(self, type, name, value, **kwargs):
        old_input = self.form.find_all('input', {'name': name})
        for old in old_input:
            old.decompose()
        old_textarea = self.form.find_all('textarea', {'name': name})
        for old in old_textarea:
            old.decompose()
        # We don't have access to the original soup object, so we
        # instantiate a new BeautifulSoup() to call new_tag().
        control = BeautifulSoup().new_tag('input')
        control['type'] = type
        control['name'] = name
        control['value'] = value
        for k, v in kwargs.items():
            control[k] = v
        self.form.append(control)
        return control

    def choose_submit(self, el):
        '''Selects the submit input (or button) element specified by 'el',
        where 'el' can be either a bs4.element.Tag or just its name attribute.
        If the element is not found or if multiple elements match, raise a
        LinkNotFoundError exception.'''
        # In a normal web browser, when a input[type=submit] is clicked,
        # all other submits aren't sent. You can use simulate this as
        # following:

        # page = browser.get(URL)
        # form_el = page.soup.form
        # form = Form(form_el)
        # submit = page.soup.select(SUBMIT_SELECTOR)[0]
        # form.choose_submit(submit)
        # url = BASE_DOMAIN + form_el.attrs['action']
        # return browser.submit(form, url)

        found = False
        inps = self.form.select('input[type="submit"], button[type="submit"]')
        for inp in inps:
            if inp == el or inp['name'] == el:
                if found:
                    raise LinkNotFoundError(
                        "Multiple submit elements match: {0}".format(el)
                    )
                found = True
                continue

            del inp['name']

        if not found:
            raise LinkNotFoundError(
                "Specified submit element not found: {0}".format(el)
            )
