/** Bounded look-ahead, consumed using simulation time rather than network timing. */
export class PlaybackBuffer<T extends { duration: number }> {
  private items: T[] = [];
  private credit = 0;
  get seconds() { return this.items.reduce((sum, item) => sum + item.duration, 0); }
  get empty() { return this.items.length === 0; }
  clear() { this.items = []; this.credit = 0; }
  push(items: T[]) { this.items.push(...items); }
  take(seconds: number): T[] {
    if (this.empty) { this.credit = 0; return []; }
    this.credit += seconds;
    const ready: T[] = [];
    while (this.items.length && this.credit + 1e-8 >= this.items[0].duration) {
      const item = this.items.shift()!;
      this.credit -= item.duration; ready.push(item);
    }
    // Never accumulate a catch-up burst across a network stall.
    if (this.empty) this.credit = 0;
    return ready;
  }
}
