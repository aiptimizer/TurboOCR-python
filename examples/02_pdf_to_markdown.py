"""PDF -> Markdown via render_to_markdown."""

from pathlib import Path

from turboocr import Client, render_to_markdown

PDF = Path(__file__).parent / "sample" / "acme_invoice.pdf"

client = Client(timeout=120.0)
response = client.recognize_pdf(
    PDF, dpi=150, layout=True, reading_order=True, include_blocks=True
)

doc = render_to_markdown(response)
print(f"pages={len(response.pages)} chars={len(doc.markdown)}")
print("--- markdown (first 500 chars) ---")
print(doc.markdown[:500])

# Output:
# pages=2 chars=1379
# --- markdown (first 500 chars) ---
# ## ACME Corporation
#
# 123 Roadrunner Way, Tumbleweed, AZ 86001 invoices@acme.example · +1 (555) 010-0182
#
# Invoice # INV-2026-00482
#
# 2026-04-15 Issue date
#
# Due date 2026-05-15
#
# Customer Coyote Logistics Ltd.
#
# Customer # C-1049
#
# ## Invoice
#
# ## Bill to
#
# Coyote Logistics Ltd.
# Attn: Accounts Payable 742 Mesa Drive, Suite 4B Flagstaff, AZ 86004
#
# ## Line items
#
# ```
# # Description Qty Unit price Amount 1 Industrial-grade Rocket Skates (model RS-9) 12 $249.00 $2,988.00 2 4 $89.50 $358.00 Anvil, 100 Ib, pai
