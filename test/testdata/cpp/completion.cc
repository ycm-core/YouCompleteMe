
struct PointInTime
{
  int point_before_time;
  double age_of_universe;
  char lifetime; // nobody will live > 128 years
};

struct Line
{
  enum { RED_AND_YELLOW, PINK_AND_GREEN } colourOfLine;
  double lengthOfLine;
};

struct PointInTimeLine
{
  PointInTime point;
  Line line;
};

static void what_is_the( PointInTimeLine* p )
{
  p->line.colourOfLine = Line::
  p->line.colourOfLine = Line::PINK_AND_GREEN;
}

static void draw_a( Line l )
{
  PointInTimeLine p = { .line = l };
  what_is_the( &p );
}
