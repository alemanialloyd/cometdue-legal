# CometDue Legal & Support

Public legal documents and support information for CometDue.

**Website:** https://alemanialloyd.github.io/cometdue-legal/

**Publisher:** Lloyd Alemania, trading as Sensei IT Solutions  
**Support and privacy:** breaksonfridays@gmail.com  
**Audience:** ages 13 and older  
**Effective date:** 2026-10-28

## Documents

- [Privacy Policy](https://alemanialloyd.github.io/cometdue-legal/privacy/)
- [Terms of Use](https://alemanialloyd.github.io/cometdue-legal/terms/)
- [Purchases & Refunds](https://alemanialloyd.github.io/cometdue-legal/refunds/)
- [Data & Deletion](https://alemanialloyd.github.io/cometdue-legal/data-deletion/)
- [Support & Contact](https://alemanialloyd.github.io/cometdue-legal/support/)
- [Open-source Licenses](https://alemanialloyd.github.io/cometdue-legal/licenses/)

## Publishing

GitHub Pages serves **main / (root)**. This repository includes `index.html`
and `.nojekyll`; no theme, custom domain, or paid plan is needed.
After updating main, inspect the **pages build and deployment** run in Actions.

## Updating content

`content/en.json` is the public copy of the content bundled by the app at
`assets/legal/en.json`. Update the app source first, then generate this site:

```powershell
python tool/legal/generate_site.py --output build/legal-site
```

Publish only that generated folder to this repository. It includes policy
content, HTML, styling and the generator. Keep the installed app's bundled
policy version in step with releases.

For a site-only checkout, regenerate with:

```powershell
python tools/generate_site.py --source content/en.json --output .
```

Update the app's canonical copy with those same changes before its next release.
Use the public Privacy Policy and Support URLs above in store listings.
Store privacy disclosures, trader verification, purchases and submission are
configured separately in the store consoles.
