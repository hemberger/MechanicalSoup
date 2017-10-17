from .utils import LinkNotFoundError
from bs4 import BeautifulSoup


class InvalidFormMethod(LinkNotFoundError):
    """This exception is raised when a method of the Form class is used
    for an html element that is of the wrong type (or is malformed).

    It is derived from :class:`LinkNotFoundError` so that a single base class
    can be used to catch all exceptions specific to this module.
    """
    pass


class Form(object):
    """The Form class is responsible for preparing html forms for submission.
    It handles the following types of elements:
    input (text, checkbox, radio), select, and textarea.

    Each type is set by a method named after the type (e.g.
    :func:`Form.set_select`), and then there are convenience methods (e.g.
    :func:`Form.set`) that do type-deduction and set the value using the
    appropriate method.

    It also handles submit-type elements using :func:`Form.select_submit`.
    """

    def __init__(self, form):
        self.form = form

    def set_input(self, data):
        """Fill-in a set of fields in a form.

        Example: filling-in a login/password form

        .. code-block:: python

           form.input({"login": username, "password": password})

        This will find the input element named "login" and give it the
        value ``username``, and the input element named "password" and
        give it the value ``password``.
        """

        for (name, value) in data.items():
            i = self.form.find("input", {"name": name})
            if not i:
                raise InvalidFormMethod("No input field named " + name)
            i["value"] = value

    def uncheck_all(self, name):
        """Remove the "checked" attribute of all input elements with
        a name attribute given by ``name``.
        """
        for option in self.form.find_all("input", {"name": name}):
            if "checked" in option.attrs:
                del option.attrs["checked"]

    def check(self, data):
        """For backwards compatibility, this method handles checkboxes
        and radio buttons in a single call. It will not uncheck any
        checkboxes unless explicitly specified by ``data``, in contrast
        with the default behavior of :func:`~Form.set_checkbox`.
        """
        for (name, value) in data.items():
            try:
                self.set_checkbox({name: value}, uncheck_others=False)
                continue
            except InvalidFormMethod:
                pass
            try:
                self.set_radio({name: value})
                continue
            except InvalidFormMethod:
                pass
            raise LinkNotFoundError("No input checkbox/radio named " + name)

    def set_checkbox(self, data, uncheck_others=True):
        """Set the "checked" attribute of input elements of type "checkbox"
        specified by ``data`` (i.e. check boxes).

        :param data: Dict of ``{name: value, ...}``. A valid input checkbox
            is identified if its name attribute matches ``name``. The box is
            then checked if its value attribute matches ``value`` or if
            ``value`` is True (or unchecked if False). To check multiple boxes,
            let ``value`` be a tuple or list.
        :param uncheck_others: If True (default), uncheck all valid input
            checkboxes not specified by ``data``. Consider setting to False if
            the checkboxes may be pre-filled by the site serving the HTML.
        """
        for (name, value) in data.items():
            print("name=", name)
            inputs = self.form.find_all("input", {"name": name},
                                        type="checkbox")
            if not inputs:
                raise InvalidFormMethod("No input checkbox named " + name)

            # uncheck if requested
            if uncheck_others:
                self.uncheck_all(name)

            # Accept individual values (int, str)
            # We just wrap them in a 1-value tuple.
            if not isinstance(value, list) and not isinstance(value, tuple):
                value = (value,)

            # Check or uncheck one or more boxes
            for choice in value:
                choice_str = str(choice)  # Allow for example literal numbers
                for i in inputs:
                    if i.attrs.get("value", "on") == choice_str:
                        i["checked"] = ""
                        break
                    # Allow specifying True or False to check/uncheck
                    elif choice is True:
                        i["checked"] = ""
                        break
                    elif choice is False:
                        if "checked" in i.attrs:
                            del i.attrs["checked"]
                        break
                else:
                    raise LinkNotFoundError(
                        "No input checkbox named %s with choice %s" %
                        (name, choice)
                    )

    def set_radio(self, data):
        """Set the "checked" attribute of input elements of type "radio"
        specified by ``data`` (i.e. select radio buttons).

        :param data: Dict of ``{name: value, ...}``. A valid input radio is
            identified if its name attribute matches ``name``. The radio is
            then checked if its value attribute matches ``value``. Only one
            radio can be checked.
        """
        for (name, value) in data.items():
            inputs = self.form.find_all("input", {"name": name}, type="radio")
            if not inputs:
                raise InvalidFormMethod("No input radio named " + name)

            # only one radio button can be checked
            self.uncheck_all(name)

            # Check the appropriate radio button (value cannot be a list/tuple)
            for i in inputs:
                if i.attrs.get("value", "on") == str(value):
                    i["checked"] = ""
                    break
            else:
                raise LinkNotFoundError(
                    "No input radio named %s with choice %s" % (name, value)
                )

    def set_textarea(self, data):
        """Set the "string" attribute of the first textarea element
        specified by ``data`` (i.e. set the text of a textarea).

        :param data: Dict of ``{name: value, ...}``. The textarea is
            found if its name attribute matches ``name``, and then its
            string attribute is set to ``value``.
        """
        for (name, value) in data.items():
            t = self.form.find("textarea", {"name": name})
            if not t:
                raise InvalidFormMethod("No textarea named " + name)
            t.string = value

    def set_select(self, data):
        """Set the "selected" attribute of the first option element
        specified by ``data`` (i.e. select an option from a dropdown).

        :param data: Dict of ``{name: value, ...}``. The select is
            found if its name attribute matches ``name``. The option
            element child with the value attribute given by ``value``
            then has its selected attribute set.
        """
        for (name, value) in data.items():
            select = self.form.find("select", {"name": name})
            if not select:
                raise InvalidFormMethod("No select named " + name)
            for option in select.find_all("option"):
                if "selected" in option.attrs:
                    del option.attrs["selected"]
            o = select.find("option", {"value": value})
            o.attrs["selected"] = "selected"

    def __setitem__(self, name, value):
        """Forwards arguments to :func:`~Form.set`."""
        return self.set(name, value)

    def set(self, name, value, force=False):
        """Set a form element identified by ``name`` to a specified ``value``.
        The type of element (input, textarea, select, ...) does not
        need to be given; it is inferred by the following methods:
        :func:`~Form.set_checkbox`,
        :func:`~Form.set_radio`,
        :func:`~Form.set_input`,
        :func:`~Form.set_textarea`,
        :func:`~Form.set_select`.

        Example: filling-in a login/password form with EULA checkbox

        .. code-block:: python

            form.set("login", username)
            form.set("password", password)
            form.set("eula-checkbox", True)

        """
        for func in ("checkbox", "radio", "input", "textarea", "select"):
            try:
                getattr(self, "set_" + func)({name: value})
                return
            except InvalidFormMethod:
                pass
        if force:
            self.new_control('input', name, value=value)
            return
        raise LinkNotFoundError("No valid element named " + name)

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

    # Aliases for backwards compatibility
    attach = set_input
    input = set_input
    textarea = set_textarea
