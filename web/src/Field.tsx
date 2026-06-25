// Małe, „głupie" kontrolki formularza. Każda ma powiązaną etykietę (htmlFor=id),
// dzięki czemu jest jednoznacznie adresowalna (m.in. dla testów Playwright).

interface NumberFieldProps {
  id: string;
  label: string;
  value: number | null;
  onChange: (value: number | null) => void;
  unit?: string;
  min?: number;
  step?: number;
  required?: boolean;
}

export function NumberField({ id, label, value, onChange, unit, min, step, required }: NumberFieldProps) {
  return (
    <label className="field" htmlFor={id}>
      <span className="field-label">
        {label}
        {unit ? <span className="unit"> ({unit})</span> : null}
      </span>
      <input
        id={id}
        name={id}
        type="number"
        inputMode="decimal"
        value={value ?? ""}
        min={min}
        step={step}
        required={required}
        onChange={(e) => onChange(e.target.value === "" ? null : Number(e.target.value))}
      />
    </label>
  );
}

interface SelectFieldProps {
  id: string;
  label: string;
  value: string;
  options: Record<string, string>;
  onChange: (value: string) => void;
  placeholder?: string;
}

export function SelectField({ id, label, value, options, onChange, placeholder }: SelectFieldProps) {
  return (
    <label className="field" htmlFor={id}>
      <span className="field-label">{label}</span>
      <select id={id} name={id} value={value} onChange={(e) => onChange(e.target.value)}>
        {placeholder !== undefined ? <option value="">{placeholder}</option> : null}
        {Object.entries(options).map(([token, text]) => (
          <option key={token} value={token}>
            {text}
          </option>
        ))}
      </select>
    </label>
  );
}

interface CheckboxFieldProps {
  id: string;
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

export function CheckboxField({ id, label, checked, onChange }: CheckboxFieldProps) {
  return (
    <label className="checkbox" htmlFor={id}>
      <input
        id={id}
        name={id}
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
      />
      <span>{label}</span>
    </label>
  );
}
