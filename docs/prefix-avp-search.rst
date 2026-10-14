Searching prefix AVPs
====================

The prefix search box supports attribute-value pairs (AVPs)::

    avp.site
    avp.site=stockholm
    avp.site!=stockholm
    avp.site="Stockholm office"
    avp.site=stockholm AND avp.environment=production
    avp.site=stockholm OR avp.site=uppsala

A bare ``avp.site`` matches a prefix with a ``site`` key, including an empty or
null value. Equality and inequality require that key to have a non-null value.
Keys and values are case-sensitive; AVPs are not inherited from parent prefixes
or VRFs. Existing prefix, tag and VRF filters can be combined with AVP terms.
The usual prefix search options can still display surrounding parent/child
prefixes as context; those are not necessarily matches themselves.

Use ``avp.`` followed by the key, and quote values containing spaces. A quoted
standalone term such as ``"avp.site"`` remains a normal free-text search.
This syntax supports keys expressible as an unquoted search word; keys with
spaces or search operators require the structured API.

The structured ``search_prefix`` query uses ``val1: "avp.site"``, with
``operator: "equals"`` or ``"not_equals"`` and the string value in ``val2``.
For key presence use ``operator: "avp_exists"`` and ``val2: true``.
No database schema change is required.
