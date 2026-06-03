from __future__ import annotations

import os


def _fmt_float(v: float) -> str:
    return f"{float(v):.3f}"


def _normalize_pointers(feedback_pointers: list[str] | None) -> list[str]:
    if not feedback_pointers:
        return []
    out: list[str] = []
    for p in feedback_pointers:
        s = str(p).strip()
        if s:
            out.append(s)
    return out


def _build_structured_context(
    *,
    grondprofiel,
    materiaal_parameters,
    geometrie,
    stabiliteitsresultaat,
    feedback_pointers: list[str],
) -> str:
    lagen = "\n".join(
        f"- Laag {i + 1}: bovenkant={laag.bovenkant}, onderkant={laag.onderkant}, materiaal={laag.materiaal}"
        for i, laag in enumerate(grondprofiel.lagen)
    )
    materialen = "\n".join(
        f"- {naam}: gamma={p.volumiek_gewicht_kN_m3} kN/m3, c={p.cohesie_kPa} kPa, phi={p.wrijvingshoek_graden}°"
        for naam, p in materiaal_parameters.per_materiaal.items()
    )
    punten = "\n".join(f"- ({pt.x}, {pt.z})" for pt in geometrie.punten)
    pointers = "\n".join(f"- {p}" for p in feedback_pointers) if feedback_pointers else "- Geen"

    return f"""
Grondwaterstand (NAP): {grondprofiel.grondwaterstand_nap}

Lagen:
{lagen}

Materiaalparameters:
{materialen}

Geometriepunten (x, z):
{punten}

Resultaat:
- Veiligheidsfactor: {stabiliteitsresultaat.veiligheidsfactor}
- Maatgevende cirkel: x0={stabiliteitsresultaat.maatgevende_cirkel_x0}, y0={stabiliteitsresultaat.maatgevende_cirkel_y0}, r={stabiliteitsresultaat.maatgevende_cirkel_r}

Feedback pointers:
{pointers}
""".strip()


def _template_report(
    *,
    grondprofiel,
    materiaal_parameters,
    geometrie,
    stabiliteitsresultaat,
    feedback_pointers: list[str],
) -> str:
    lines: list[str] = []

    lines.append("## 1. Uitgangspunten")
    lines.append(f"- Grondwaterstand (NAP): {_fmt_float(grondprofiel.grondwaterstand_nap)} m")
    lines.append("- Grondprofiel:")
    for i, laag in enumerate(grondprofiel.lagen, start=1):
        lines.append(
            f"  - Laag {i}: bovenkant {_fmt_float(laag.bovenkant)} m, "
            f"onderkant {_fmt_float(laag.onderkant)} m, materiaal '{laag.materiaal}'"
        )
    lines.append("- Materiaalparameters:")
    for naam, p in materiaal_parameters.per_materiaal.items():
        lines.append(
            f"  - {naam}: γ={_fmt_float(p.volumiek_gewicht_kN_m3)} kN/m³, "
            f"c={_fmt_float(p.cohesie_kPa)} kPa, φ={_fmt_float(p.wrijvingshoek_graden)}°"
        )
    lines.append("- Geometriepunten (x, z):")
    for pt in geometrie.punten:
        lines.append(f"  - ({_fmt_float(pt.x)}, {_fmt_float(pt.z)})")

    lines.append("\n## 2. Modellering")
    lines.append("- Sterktemodel: Mohr-Coulomb.")
    lines.append("- Stabiliteitsmethode: Bishop (circular slip surface search).")

    lines.append("\n## 3. Resultaten")
    lines.append(f"- Veiligheidsfactor (FoS): {_fmt_float(stabiliteitsresultaat.veiligheidsfactor)}")
    lines.append(
        "- Maatgevende glijcirkel: "
        f"x0={_fmt_float(stabiliteitsresultaat.maatgevende_cirkel_x0)}, "
        f"y0={_fmt_float(stabiliteitsresultaat.maatgevende_cirkel_y0)}, "
        f"r={_fmt_float(stabiliteitsresultaat.maatgevende_cirkel_r)}"
    )

    lines.append("\n## 4. Conclusie")
    if stabiliteitsresultaat.veiligheidsfactor >= 1.0:
        lines.append("- De berekening geeft indicatief een stabiele situatie (FoS ≥ 1.0).")
    else:
        lines.append("- De berekening geeft indicatief een onvoldoende stabiele situatie (FoS < 1.0).")

    if feedback_pointers:
        lines.append("- Verwerkte aandachtspunten uit gebruikersfeedback:")
        for p in feedback_pointers:
            lines.append(f"  - {p}")

    return "\n".join(lines)


def _try_openai_report(system_prompt: str, user_prompt: str) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI

        model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        base_url = os.getenv("OPENAI_BASE_URL") or None
        client = OpenAI(api_key=api_key, base_url=base_url)

        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content
        return str(content).strip() if content else None
    except Exception as exc:
        print(f"OpenAI rapportgeneratie mislukt, fallback naar templates: {exc}")
        return None


def _try_anthropic_report(system_prompt: str, user_prompt: str) -> str | None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        from anthropic import Anthropic

        model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
        client = Anthropic(api_key=api_key)

        response = client.messages.create(
            model=model,
            max_tokens=1400,
            temperature=0.2,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        parts: list[str] = []
        for block in response.content:
            text = getattr(block, "text", None)
            if text:
                parts.append(str(text))
        output = "\n".join(parts).strip()
        return output or None
    except Exception as exc:
        print(f"Anthropic rapportgeneratie mislukt, fallback naar templates: {exc}")
        return None


def _try_openrouter_report(system_prompt: str, user_prompt: str) -> str | None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI

        model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        client = OpenAI(api_key=api_key, base_url=base_url)

        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content
        return str(content).strip() if content else None
    except Exception as exc:
        print(f"OpenRouter rapportgeneratie mislukt, fallback naar templates: {exc}")
        return None


def _try_ai_report_by_key_name(system_prompt: str, user_prompt: str) -> str | None:
    # Keuze op basis van naam van beschikbare API key env var.
    if os.getenv("OPENAI_API_KEY"):
        return _try_openai_report(system_prompt, user_prompt)
    if os.getenv("ANTHROPIC_API_KEY"):
        return _try_anthropic_report(system_prompt, user_prompt)
    if os.getenv("OPENROUTER_API_KEY"):
        return _try_openrouter_report(system_prompt, user_prompt)
    return None


def genereer_rapport(
    *,
    grondprofiel,
    materiaal_parameters,
    geometrie,
    stabiliteitsresultaat,
    feedback_pointers: list[str] | None = None,
) -> str:
    pointers = _normalize_pointers(feedback_pointers)

    system_prompt = (
        "Je bent een geotechnisch rapportassistent. "
        "Schrijf compact, feitelijk en zonder extra aannames. "
        "Gebruik exact deze structuur met koppen: "
        "1. Uitgangspunten, 2. Modellering, 3. Resultaten, 4. Conclusie."
    )
    user_prompt = _build_structured_context(
        grondprofiel=grondprofiel,
        materiaal_parameters=materiaal_parameters,
        geometrie=geometrie,
        stabiliteitsresultaat=stabiliteitsresultaat,
        feedback_pointers=pointers,
    )

    ai_report = _try_ai_report_by_key_name(system_prompt, user_prompt)
    if ai_report:
        return ai_report

    return _template_report(
        grondprofiel=grondprofiel,
        materiaal_parameters=materiaal_parameters,
        geometrie=geometrie,
        stabiliteitsresultaat=stabiliteitsresultaat,
        feedback_pointers=pointers,
    )
