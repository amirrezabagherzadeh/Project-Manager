import { ProductApp } from "@/components/product/product-app"

export default async function InvitationPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params
  return <ProductApp inviteToken={token} />
}
