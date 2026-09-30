"""Trading losses brought forward: box 160 (same trade) and box 285 (total profits)."""

from decimal import Decimal

import pytest
from answers import boxes, compute
from test_hmrc_xml import build, make_return

from open_ct600.hmrc.validate import validate_return

SMALL_TRADE = {"turnover": 10_000, "interest_income": 50_000}


def losses(total: int, before_april_2017: int = 0) -> dict:
    return {
        "losses_brought_forward": total,
        "losses_brought_forward_before_april_2017": before_april_2017,
    }


def test_losses_from_april_2017_are_set_against_total_profits_in_box_285():
    # CT600 guide box 160/285; CTA 2010 s45A. Trading profit 10,000 and interest 50,000:
    # the 40,000 of post-2017 losses relieve total profits (box 285), leaving 20,000.
    computation = compute(profit_and_loss=SMALL_TRADE, tax_adjustments=losses(40_000))

    result = boxes(computation)
    assert "160" not in result or result["160"] == 0
    assert (result["165"], result["235"]) == (10_000, 60_000)
    assert (result["285"], result["295"], result["300"], result["315"]) == (
        40_000,
        40_000,
        20_000,
        20_000,
    )
    assert computation.losses_carried_forward == 0


def test_losses_from_before_april_2017_only_relieve_the_trade_in_box_160():
    # CTA 2010 s45: set against profits of the same trade only.
    computation = compute(profit_and_loss=SMALL_TRADE, tax_adjustments=losses(40_000, 40_000))

    result = boxes(computation)
    assert (result["160"], result["165"], result["315"]) == (10_000, 0, 50_000)
    assert "285" not in result
    assert computation.losses_carried_forward == 30_000


def test_older_losses_go_first_against_the_trade_and_newer_ones_against_the_rest():
    # 5,000 from before April 2017 against the trade; 35,000 later ones against total profits.
    computation = compute(profit_and_loss=SMALL_TRADE, tax_adjustments=losses(40_000, 5_000))

    result = boxes(computation)
    assert (result["160"], result["285"], result["300"]) == (5_000, 35_000, 20_000)


def test_losses_larger_than_total_profits_carry_forward_the_rest():
    computation = compute(profit_and_loss=SMALL_TRADE, tax_adjustments=losses(100_000))

    result = boxes(computation)
    assert (result["285"], result["315"], result["440"]) == (60_000, 0, Decimal("0.00"))
    assert computation.losses_carried_forward == 40_000


@pytest.mark.parametrize(
    "adjustments", [losses(40_000), losses(40_000, 40_000), losses(40_000, 5_000), losses(100_000)]
)
def test_loss_relief_returns_are_accepted_by_hmrc(adjustments):
    ct600 = make_return(profit_and_loss=SMALL_TRADE, tax_adjustments=adjustments)

    assert validate_return(build(ct600)) == []
