package com.gathin.tvhome;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.Locale;
import java.util.TimeZone;

/**
 * Android 6 没有 java.time（API 26 才有），而项目里只用到很小一块：
 * 今天、从 "yyyy-MM-dd" 解析、第几天、日期比较，以及某天的时区偏移。
 * 这里用 Calendar 实现同样语义，签名对齐调用点，方便以后换回 java.time。
 */
final class JTime {

    private JTime() {}

    /** 本地时区的"今天"，只保留年月日。 */
    static Date today() {
        Calendar c = Calendar.getInstance();
        return atMidnight(c);
    }

    /** 解析 "yyyy-MM-dd"，失败返回 null（对应原来捕获 DateTimeParseException）。 */
    static Date parseDate(String text) {
        if (text == null) return null;
        SimpleDateFormat f = new SimpleDateFormat("yyyy-MM-dd", Locale.ROOT);
        f.setLenient(false);
        try {
            return f.parse(text.trim());
        } catch (ParseException e) {
            return null;
        }
    }

    /** 一年中的第几天，1 起算，与 LocalDate.getDayOfYear() 一致。 */
    static int dayOfYear(Date date) {
        Calendar c = Calendar.getInstance();
        c.setTime(date);
        return c.get(Calendar.DAY_OF_YEAR);
    }

    /** a 是否严格晚于 b（对应 LocalDate.isAfter）。 */
    static boolean isAfter(Date a, Date b) {
        return atMidnight(toCal(a)).after(atMidnight(toCal(b)));
    }

    /**
     * 该日期在当天中午 12 点的时区偏移，单位分钟。
     * 对应 zone.getRules().getOffset(date.atTime(12,0)).getTotalSeconds()/60。
     */
    static int offsetMinutesAtNoon(Date date, TimeZone zone) {
        Calendar c = Calendar.getInstance(zone);
        c.setTime(date);
        c.set(Calendar.HOUR_OF_DAY, 12);
        c.set(Calendar.MINUTE, 0);
        c.set(Calendar.SECOND, 0);
        c.set(Calendar.MILLISECOND, 0);
        return zone.getOffset(c.getTimeInMillis()) / 60000;
    }

    private static Calendar toCal(Date d) {
        Calendar c = Calendar.getInstance();
        c.setTime(d);
        return c;
    }

    private static Date atMidnight(Calendar c) {
        c.set(Calendar.HOUR_OF_DAY, 0);
        c.set(Calendar.MINUTE, 0);
        c.set(Calendar.SECOND, 0);
        c.set(Calendar.MILLISECOND, 0);
        return c.getTime();
    }
}
