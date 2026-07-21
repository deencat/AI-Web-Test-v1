from app.services.tier2_hybrid import Tier2HybridExecutor

e = object.__new__(Tier2HybridExecutor)
instr = "Click $228 / 36 month plan"
print(repr(instr))
print("price", e._extract_plan_price(instr))
print("variants", e._extract_three_hk_promotion_text_variants(instr))
print(
    "is_uat_url",
    e._is_three_hk_promotion_card_click(
        "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en", instr, "click"
    ),
)
print(
    "is_crm_page_match",
    e._is_three_hk_promotion_card_click(
        "https://sales-portal-ogp-crm.apps.ocpppd.three.com.hk/sales/voucher/select-plan",
        instr,
        "click",
        looks_like_three_hk_promotion_page=True,
    ),
)
