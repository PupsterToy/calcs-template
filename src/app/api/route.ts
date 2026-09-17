import { NextResponse } from "next/server";

// Статический маршрут: совместим и с обычной сборкой, и с output: "export"
// (GitHub Pages), где динамические серверные функции недоступны.
export const dynamic = "force-static";

export async function GET() {
  return NextResponse.json({ message: "Hello, world!" });
}