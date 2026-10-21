package com.gathin.tvhome;

import android.content.Context;
import android.graphics.Typeface;

/**
 * Android 8.0 之前没有 res/font 支持，字体只能从 assets 读取。
 * 这里集中缓存，避免每次 new TextView 都重新解析 ttf。
 */
final class Outfit {
    private static Typeface base;

    private Outfit() {}

    private static Typeface base(Context context) {
        if (base == null) {
            try {
                base = Typeface.createFromAsset(context.getAssets(), "fonts/outfit.ttf");
            } catch (RuntimeException e) {
                base = Typeface.SANS_SERIF;
            }
        }
        return base;
    }

    static Typeface REGULAR(Context context) {
        return Typeface.create(base(context), Typeface.NORMAL);
    }

    static Typeface MEDIUM(Context context) {
        return Typeface.create(base(context), Typeface.NORMAL);
    }

    static Typeface LIGHT(Context context) {
        return Typeface.create(base(context), Typeface.NORMAL);
    }

    static Typeface EXTRALIGHT(Context context) {
        return Typeface.create(base(context), Typeface.NORMAL);
    }
}
