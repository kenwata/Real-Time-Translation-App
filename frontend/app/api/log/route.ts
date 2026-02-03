import { NextRequest, NextResponse } from 'next/server';
import logger from '@/lib/logger';

export async function POST(req: NextRequest) {
    try {
        const body = await req.json();
        const { level, message, meta } = body;

        if (level === 'error') {
            logger.error(message, meta);
        } else if (level === 'warn') {
            logger.warn(message, meta);
        } else {
            logger.info(message, meta);
        }

        return NextResponse.json({ success: true });
    } catch (error) {
        console.error('Failed to log client message', error);
        return NextResponse.json({ success: false }, { status: 500 });
    }
}
