/* Trig Cond in another order on the knob (notes/70), in the freed 48x22 sprite mask 0x40152d38 (192 bytes,
 * tools/sprites.py): the code, then the 64-byte order the generator fills. */
SECTIONS
{
  .cave 0x40152d38 : {
    *(.text.trig_cond_order) . = ALIGN(2); *(.data.trig_cond_order)
  }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
