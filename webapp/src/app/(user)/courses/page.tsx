"use client";

import { useState } from "react";
import Link from "next/link";
import { Search, Star, Clock, BookOpen, Users, ChevronRight } from "lucide-react";
import { useSession } from "@/lib/session";

export default function CoursesCatalogPage() {
  const { courses } = useSession();
  const [selectedCategory, setSelectedCategory] = useState<string>("Barchasi");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const categories = ["Barchasi", ...Array.from(new Set(courses.map((course) => course.category)))];

  const filteredCourses = courses.filter((course) => {
    const matchesCategory =
      selectedCategory === "Barchasi" || course.category === selectedCategory;
    const matchesSearch =
      course.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      course.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-foreground">O&apos;quv kurslari</h1>
        <p className="text-xs text-muted-foreground mt-0.5">
          Malaka oshirish va sohaviy ta&apos;lim dasturlari
        </p>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Kurs nomi yoki mavzu bo'yicha qidiring..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-card border border-border/70 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary transition-all"
        />
      </div>

      {/* Category Pills */}
      <div className="flex space-x-2 overflow-x-auto pb-1 scrollbar-none -mx-1 px-1">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
              selectedCategory === cat
                ? "bg-primary text-primary-foreground shadow-sm scale-105"
                : "bg-secondary text-muted-foreground hover:text-foreground"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Courses List */}
      <div className="space-y-3 pt-1">
        {filteredCourses.length === 0 && (
          <p className="text-sm text-muted-foreground">Bu bo&apos;limda kurs topilmadi.</p>
        )}
        {filteredCourses.map((course) => (
          <Link
            key={course.id}
            href={`/courses/${course.id}`}
            className="block bg-card hover:bg-card/90 border border-border/70 rounded-2xl overflow-hidden shadow-sm transition-all duration-200 active:scale-[0.99] group"
          >
            <div className="relative h-36 w-full overflow-hidden bg-muted">
              {course.coverImage ? (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img
                  src={course.coverImage}
                  alt={course.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
              ) : (
                <div className="w-full h-full bg-secondary" />
              )}
              <div className="absolute inset-0 bg-gradient-to-t from-background via-background/20 to-transparent" />
              <span className="absolute top-3 left-3 bg-background/80 backdrop-blur-md text-[11px] font-semibold text-primary px-2.5 py-0.5 rounded-full border border-border/40">
                {course.category}
              </span>

              {course.progressPercentage !== undefined && course.progressPercentage > 0 && (
                <span className="absolute top-3 right-3 bg-emerald-500/90 text-white text-[11px] font-bold px-2 py-0.5 rounded-full shadow">
                  {course.progressPercentage}% yakunlangan
                </span>
              )}
            </div>

            <div className="p-4 space-y-2">
              <h3 className="font-bold text-base text-foreground tracking-tight line-clamp-1 group-hover:text-primary transition-colors">
                {course.title}
              </h3>
              <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                {course.description}
              </p>

              <div className="pt-2 flex items-center justify-between text-xs text-muted-foreground border-t border-border/40">
                <div className="flex items-center space-x-3">
                  <span className="flex items-center space-x-1">
                    <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                    <span className="font-semibold text-foreground">{course.rating}</span>
                  </span>
                  <span className="flex items-center space-x-1">
                    <BookOpen className="w-3.5 h-3.5" />
                    <span>{course.lessonsCount} dars</span>
                  </span>
                  <span className="flex items-center space-x-1">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{course.durationHours} soat</span>
                  </span>
                </div>

                <div className="flex items-center text-primary font-semibold text-xs">
                  <span>Kirish</span>
                  <ChevronRight className="w-4 h-4" />
                </div>
              </div>
            </div>
          </Link>
        ))}

        {filteredCourses.length === 0 && (
          <div className="text-center py-12 space-y-2">
            <BookOpen className="w-10 h-10 text-muted-foreground/50 mx-auto" />
            <p className="text-sm font-medium text-foreground">Bunday kurs topilmadi</p>
            <p className="text-xs text-muted-foreground">Boshqa kalit so&apos;z yoki toifa tanlab ko&apos;ring</p>
          </div>
        )}
      </div>
    </div>
  );
}
