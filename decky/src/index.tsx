// Scaler Assistant for Decky Loader: choose DLSS 3.7 (HelixSR), FSR 4.1 or FSR 3 per Steam
// game from the Quick Access menu. All the work is done by the Python backend (the same
// scaler_assistant package as the desktop app); this file is the panel and its dialogs.

import {
  ButtonItem,
  ConfirmModal,
  DialogBody,
  DialogButton,
  DialogCheckbox,
  DialogControlsSection,
  DialogControlsSectionHeader,
  DialogFooter,
  DialogHeader,
  DropdownItem,
  Field,
  Focusable,
  ModalRoot,
  PanelSection,
  PanelSectionRow,
  ProgressBarWithInfo,
  showModal,
  staticClasses,
  ToggleField,
} from "@decky/ui";
import {
  addEventListener,
  callable,
  definePlugin,
  openFilePicker,
  removeEventListener,
  toaster,
} from "@decky/api";
import { CSSProperties, ReactNode, useEffect, useState } from "react";
import { FaLayerGroup } from "react-icons/fa";

// ---- backend ---------------------------------------------------------------------------------

interface Choice { id: string; label: string; hint: string; current: boolean; recommended: boolean }
interface LiveLine { label: string; detail: string; active: boolean }
interface Live { headline: string; tone: string; lines: LiveLine[]; notes: string[]; loaded: boolean }
interface Game {
  app_id: number; name: string; installed: boolean; choice: string | null; label: string;
  tone: string; detail: string; upscaler: string; api: string; upscalers: string[];
  anti_cheat: string[]; outdated: boolean; issues: string[]; notes: string[]; hint: string;
  opti_name: string; opti_possible: boolean; launch_options: string; shows_launch: boolean;
  has_log: boolean; choices: Choice[]; running: Live | null;
  fg: boolean | null; fg_block: string;   // HelixSR frame generation (null: not offered)
}
interface Component {
  key: string; name: string; version: string; size: number; ready: boolean; wanted: boolean;
  description: string; licence: string; project: string;
}
interface Downloads {
  items: Component[]; missing: string[]; build: string; builds: [string, string][]; intro: string;
}
interface HelixSR { ready: boolean; pill: string; path: string; message: string }
interface Overview {
  version: string; language: string; languages: [string, string][]; games: Game[];
  unsupported: number; running: number[]; outdated: number; helixsr: HelixSR;
  downloads: Downloads; gpu: string; toast: boolean; home: string; log: string[];
}
interface Result { ok: boolean; kind?: string; message: string; keys?: string[] }
interface Step { kind: string; title?: string; text: string; ok?: string; keys?: string[] }
interface Plan { choice: string; label: string; steps: Step[] }
interface Removal { title: string; text: string; ok: string; settings: string }
interface OptiNames {
  title: string; intro: string; hint: string; current: string; chosen: string; auto: string;
  options: [string, string][];
}

const start = callable<[steamLanguage: string], { strings: Record<string, string>; toast: boolean }>("start");
const setLanguageCall = callable<[code: string], { strings: Record<string, string> }>("set_language");
const overviewCall = callable<[rescan: boolean], Overview>("overview");
const planCall = callable<[appId: number, choice: string], Plan>("plan");
const lossyText = callable<[], string>("lossy_text");
const acceptLossy = callable<[], void>("accept_lossy");
const applyCall = callable<[appId: number, choice: string], Result>("apply");
const removalCall = callable<[appId: number], Removal>("removal");
const setFgCall = callable<[appId: number, on: boolean], Result>("set_frame_generation");
const uninstallCall = callable<[appId: number, removeSettings: boolean], Result>("uninstall");
const updateAllCall = callable<[], Result>("update_all");
const downloadCall = callable<[keys: string[]], Result>("download");
const removeDownloads = callable<[], Result>("remove_downloads");
const setFsr4Build = callable<[value: string], void>("set_fsr4_build");
const optiNamesCall = callable<[appId: number], OptiNames>("opti_names");
const setOptiName = callable<[appId: number, name: string], Result>("set_opti_name");
const setHelixsrFolder = callable<[path: string], Result>("set_helixsr_folder");
const logText = callable<[appId: number], { path: string; text: string }>("log_text");
const setToast = callable<[enabled: boolean], void>("set_toast");
const runtimeCall = callable<[appId: number], Game | null>("runtime");

// ---- strings (from the backend's i18n, 12 languages) ----------------------------------------

let S: Record<string, string> = {};
let toastEnabled = true;
let ready: Promise<void> | null = null;

function t(key: string, values: Record<string, string | number> = {}): string {
  const text = S[key] ?? key;
  return text.replace(/\{(\w+)\}/g, (all, name) => (name in values ? String(values[name]) : all));
}

function init(): Promise<void> {
  if (!ready) {
    ready = (async () => {
      let language = "english";
      try {
        language = await SteamClient.Settings.GetCurrentLanguage();
      } catch (e) { /* older Steam: English */ }
      const result = await start(language);
      S = result.strings;
      toastEnabled = result.toast;
    })();
  }
  return ready;
}

// ---- busy state shared by the panel and the dialogs --------------------------------------------

interface Busy { text: string; progress: number }
let busy: Busy = { text: "", progress: -1 };
const busyListeners = new Set<(b: Busy) => void>();
function setBusy(next: Busy) {
  busy = next;
  busyListeners.forEach((fn) => fn(next));
}
function useBusy(): Busy {
  const [state, setState] = useState(busy);
  useEffect(() => {
    busyListeners.add(setState);
    return () => { busyListeners.delete(setState); };
  }, []);
  return state;
}
async function working<T>(text: string, fn: () => Promise<T>): Promise<T> {
  setBusy({ text, progress: -1 });
  try {
    return await fn();
  } finally {
    setBusy({ text: "", progress: -1 });
  }
}

// ---- small dialogs -----------------------------------------------------------------------------

const textBox: CSSProperties = { whiteSpace: "pre-wrap", maxHeight: "48vh", overflowY: "auto" };
const muted: CSSProperties = { color: "#8b929a", fontSize: "12px", whiteSpace: "pre-wrap" };
const TONES: Record<string, string> = {
  ok: "#27d4b3", warn: "#f2c14e", info: "#7cc0ff", orange: "#ff8a87", idle: "#8b929a",
};

function ask(title: string, text: ReactNode, ok: string): Promise<boolean> {
  return new Promise((resolve) => {
    let answered = false;
    const done = (value: boolean) => { if (!answered) { answered = true; resolve(value); } };
    showModal(
      <ConfirmModal strTitle={title} strOKButtonText={ok} strCancelButtonText={t("cancel")}
        onOK={() => done(true)} onCancel={() => done(false)} closeModal={() => done(false)}>
        <div style={textBox}>{text}</div>
      </ConfirmModal>,
    );
  });
}

function tell(title: string, text: string): Promise<void> {
  return new Promise((resolve) => {
    showModal(
      <ConfirmModal strTitle={title} bAlertDialog strOKButtonText={t("ok")}
        onOK={() => resolve()} onCancel={() => resolve()} closeModal={() => resolve()}>
        <div style={textBox}>{text}</div>
      </ConfirmModal>,
    );
  });
}

async function report(result: Result) {
  if (result.message) {
    await tell(result.ok ? t("deck_done") : t("deck_failed"), result.message);
  }
}

// ---- flows -------------------------------------------------------------------------------------

async function download(keys: string[]): Promise<Result> {
  setBusy({ text: t("busy_download"), progress: 0 });
  try {
    return await downloadCall(keys);
  } finally {
    setBusy({ text: "", progress: -1 });
  }
}

async function choose(game: Game, choice: string): Promise<boolean> {
  const plan = await working(t("busy_check", { name: game.name }), () => planCall(game.app_id, choice));
  for (const step of plan.steps) {
    if (step.kind === "helixsr") {
      await tell(step.title ?? "", step.text);
      return false;
    }
    if (step.kind === "confirm" && !(await ask(step.title ?? "", step.text, step.ok ?? t("ok")))) {
      return false;
    }
    if (step.kind === "download") {
      if (!(await ask(step.title ?? "", step.text, step.ok ?? t("ok")))) return false;
      const result = await download(step.keys ?? []);
      if (!result.ok) { await report(result); return false; }
    }
    if (step.kind === "lossy") {
      const body = await lossyText();
      if (!(await ask(step.title ?? "", `${step.text}\n\n${body}`, step.ok ?? t("ok")))) return false;
      await acceptLossy();
    }
  }
  let result = await working(t("busy_install", { name: game.name }), () => applyCall(game.app_id, choice));
  if (!result.ok && result.kind === "download" && result.keys) {
    const fetched = await download(result.keys);
    if (!fetched.ok) { await report(fetched); return false; }
    result = await working(t("busy_install", { name: game.name }), () => applyCall(game.app_id, choice));
  }
  await report(result);
  return result.ok;
}

async function remove(game: Game): Promise<boolean> {
  const info = await removalCall(game.app_id);
  let removeSettings = false;
  const confirmed = await ask(info.title, (
    <>
      <div>{info.text}</div>
      {info.settings && (
        <DialogCheckbox label={info.settings} onChange={(v) => { removeSettings = v; }} />
      )}
    </>
  ), info.ok);
  if (!confirmed) return false;
  const result = await working(t("busy_remove", { name: game.name }),
    () => uninstallCall(game.app_id, removeSettings));
  await report(result);
  return result.ok;
}

// ---- game dialog -------------------------------------------------------------------------------

function Chip({ text, tone }: { text: string; tone: string }) {
  const color = TONES[tone] ?? TONES.idle;
  return (
    <span style={{
      color, border: `1px solid ${color}66`, background: `${color}1f`, borderRadius: "10px",
      padding: "1px 8px", fontSize: "12px", whiteSpace: "nowrap",
    }}>{text}</span>
  );
}

function LiveState({ live }: { live: Live }) {
  return (
    <div style={{ fontSize: "12px", lineHeight: "18px" }}>
      <div style={{ color: TONES[live.tone] ?? TONES.warn, fontWeight: 600 }}>{live.headline}</div>
      {live.lines.map((line, i) => (
        <div key={i} style={{ color: line.active ? "#dcdedf" : "#8b929a" }}>
          {line.active ? "✓" : "✗"} {line.label}{line.detail ? ` — ${line.detail}` : ""}
        </div>
      ))}
      {live.notes.map((note, i) => <div key={`n${i}`} style={{ color: TONES.warn }}>⚠ {note}</div>)}
    </div>
  );
}

function GameModal({ game, closeModal, refresh }: {
  game: Game; closeModal?: () => void; refresh: () => void;
}) {
  const run = async (fn: () => Promise<boolean>) => {
    closeModal?.();
    await fn();
    refresh();
  };
  const facts: [string, string][] = [
    [t("det_api"), game.api || "—"],
    [t("det_upscalers"), game.upscalers.join(" · ") || "—"],
  ];
  if (game.opti_name) facts.push(["OptiScaler", game.opti_name]);
  if (game.shows_launch) facts.push([t("det_launch"), game.launch_options || t("empty")]);
  const fixLabel = game.issues.length ? t("btn_repair") : t("btn_update");
  return (
    <ModalRoot closeModal={closeModal}>
      <DialogHeader>{game.name}</DialogHeader>
      <DialogBody>
        <div style={{ display: "flex", gap: "8px", alignItems: "center", marginBottom: "8px" }}>
          <Chip text={game.label} tone={game.tone} />
          <span style={muted}>{game.detail}</span>
        </div>
        {game.running && <LiveState live={game.running} />}
        {[...game.notes, ...game.issues].map((note, i) => (
          <div key={i} style={{ color: TONES.warn, fontSize: "12px" }}>⚠ {note}</div>
        ))}
        {game.anti_cheat.length > 0 && (
          <div style={{ color: TONES.warn, fontSize: "12px" }}>⚠ {game.anti_cheat.join(", ")} — {t("ups_anti_cheat")}</div>
        )}
        {game.hint && <div style={{ ...muted, marginTop: "6px" }}>{game.hint}</div>}
        <div style={{ marginTop: "8px" }}>
          {facts.map(([name, value]) => (
            <div key={name} style={{ fontSize: "12px" }}>
              <span style={{ color: "#8b929a" }}>{name}: </span>{value}
            </div>
          ))}
        </div>
        <DialogControlsSection>
          <DialogControlsSectionHeader>{game.installed ? t("btn_change") : t("btn_choose")}</DialogControlsSectionHeader>
          <Focusable style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {game.installed && (game.outdated || game.issues.length > 0) && game.choice && (
              <DialogButton onClick={() => run(() => choose(game, game.choice as string))}>
                {fixLabel} — {game.label}
              </DialogButton>
            )}
            {game.choices.map((choice, index) => (
              <Field key={choice.id || `blocked-${index}`}
                label={<span style={{
                  opacity: choice.id ? 1 : 0.45,
                  color: choice.recommended ? TONES.ok : undefined,
                }}>{`${choice.current ? "✓ " : ""}${choice.label}`}</span>}
                description={<span style={{ whiteSpace: "pre-wrap", opacity: choice.id ? 1 : 0.6 }}>{choice.hint}</span>}
                bottomSeparator="none" childrenLayout="inline"
                focusable={!choice.id || choice.current} >
                {choice.id && !choice.current && (
                  <DialogButton style={{ minWidth: "120px" }}
                    onClick={() => run(() => choose(game, choice.id))}>
                    {t("deck_use")}
                  </DialogButton>
                )}
              </Field>
            ))}
          </Focusable>
        </DialogControlsSection>
        {game.fg !== null && (
          <DialogControlsSection>
            <ToggleField label={t("fg_switch")} checked={game.fg} disabled={!!game.fg_block}
              description={<span style={{ whiteSpace: "pre-wrap" }}>
                {game.fg_block ? `⚠ ${game.fg_block}\n${t("fg_switch_tip")}` : t("fg_switch_tip")}</span>}
              onChange={(on) => run(async () => {
                const result = await working(t("busy_fg"), () => setFgCall(game.app_id, on));
                await report(result);
                return result.ok;
              })} />
          </DialogControlsSection>
        )}
        <DialogControlsSection>
          <Focusable style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
            {game.opti_possible && (
              <DialogButton style={{ width: "auto" }}
                onClick={() => { closeModal?.(); showOptiName(game, refresh); }}>
                {game.opti_name ? t("menu_opti_name", { name: game.opti_name }) : t("menu_opti_name_auto")}
              </DialogButton>
            )}
            {game.has_log && (
              <DialogButton style={{ width: "auto" }} onClick={() => showLog(game)}>
                {t("menu_log", { file: game.upscaler === "helixsr" ? "helixsr.log" : "OptiScaler.log" })}
              </DialogButton>
            )}
            {game.installed && (
              <DialogButton style={{ width: "auto", color: TONES.orange }}
                onClick={() => run(() => remove(game))}>
                {t("btn_remove")}
              </DialogButton>
            )}
          </Focusable>
        </DialogControlsSection>
        {game.upscaler === "helixsr" && <div style={{ ...muted, marginTop: "8px" }}>{t("deck_settings_desktop")}</div>}
      </DialogBody>
      <DialogFooter>
        <DialogButton onClick={() => closeModal?.()}>{t("close")}</DialogButton>
      </DialogFooter>
    </ModalRoot>
  );
}

function showGame(game: Game, refresh: () => void) {
  showModal(<GameModal game={game} refresh={refresh} />);
}

function OptiNameModal({ info, game, closeModal, refresh }: {
  info: OptiNames; game: Game; closeModal?: () => void; refresh: () => void;
}) {
  const [value, setValue] = useState(info.chosen);
  return (
    <ConfirmModal strTitle={info.title} strOKButtonText={t("btn_save")}
      strCancelButtonText={t("cancel")} closeModal={closeModal}
      onOK={async () => {
        if (value === info.chosen) return;
        const result = await working(t("busy_install", { name: game.name }),
          () => setOptiName(game.app_id, value));
        await report(result);
        refresh();
      }}>
      <div style={muted}>{info.intro}</div>
      <DropdownItem rgOptions={info.options.map(([data, label]) => ({ data, label }))}
        selectedOption={value} onChange={(option) => setValue(option.data)} />
      {info.current && <div style={muted}>{t("on_current", { name: info.current })}</div>}
      <div style={muted}>{info.hint}</div>
    </ConfirmModal>
  );
}

async function showOptiName(game: Game, refresh: () => void) {
  const info = await optiNamesCall(game.app_id);
  showModal(<OptiNameModal info={info} game={game} refresh={refresh} />);
}

async function showLog(game: Game) {
  const log = await logText(game.app_id);
  await tell(log.path || t("menu_log", { file: "" }), log.text || t("empty"));
}

function DownloadsModal({ downloads, closeModal, refresh }: {
  downloads: Downloads; closeModal?: () => void; refresh: () => void;
}) {
  const [build, setBuild] = useState(downloads.build);
  return (
    <ModalRoot closeModal={closeModal}>
      <DialogHeader>{t("dl_title")}</DialogHeader>
      <DialogBody>
        <div style={muted}>{downloads.intro}</div>
        {downloads.items.map((item) => (
          <Field key={item.key} label={`${item.name} · ${item.version}`} bottomSeparator="standard"
            description={<>
              <div style={{ color: item.ready ? TONES.ok : "#8b929a" }}>
                {item.ready ? `✓ ${t("dl_ready")}` : t("dl_missing", { size: `${item.size} MB` })}
              </div>
              <div style={muted}>{item.description}</div>
              <div style={muted}>{item.licence} · {item.project.replace("https://", "")}</div>
            </>} />
        ))}
        <DropdownItem label={t("dl_build")} description={t("dl_build_hint")}
          rgOptions={downloads.builds.map(([data, label]) => ({ data, label }))}
          selectedOption={build}
          onChange={async (option) => { setBuild(option.data); await setFsr4Build(option.data); refresh(); }} />
      </DialogBody>
      <DialogFooter>
        <Focusable style={{ display: "flex", gap: "8px" }}>
          <DialogButton disabled={downloads.missing.length === 0} onClick={async () => {
            closeModal?.();
            await report(await download(downloads.missing));
            refresh();
          }}>{downloads.missing.length ? t("dl_get") : t("dl_all_ready")}</DialogButton>
          <DialogButton disabled={!downloads.items.some((i) => i.ready)} onClick={async () => {
            closeModal?.();
            if (await ask(t("dl_remove"), t("dl_remove_q"), t("dl_remove"))) {
              await report(await removeDownloads());
              refresh();
            }
          }}>{t("dl_remove")}</DialogButton>
          <DialogButton onClick={() => closeModal?.()}>{t("close")}</DialogButton>
        </Focusable>
      </DialogFooter>
    </ModalRoot>
  );
}

// ---- the Quick Access panel ------------------------------------------------------------------

function GameRow({ game, refresh }: { game: Game; refresh: () => void }) {
  return (
    <PanelSectionRow>
      <ButtonItem layout="below" onClick={() => showGame(game, refresh)}
        description={
          <div>
            <div style={{ display: "flex", gap: "6px", alignItems: "center", flexWrap: "wrap" }}>
              <Chip text={game.label} tone={game.tone} />
              {game.outdated && <Chip text={t("btn_update")} tone="info" />}
              {game.issues.length > 0 && <Chip text={`⚠ ${game.issues.length}`} tone="warn" />}
            </div>
            {game.running && <div style={{ marginTop: "4px" }}><LiveState live={game.running} /></div>}
          </div>
        }>
        {game.name}
      </ButtonItem>
    </PanelSectionRow>
  );
}

function Content() {
  const [strings, setStrings] = useState(S);
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState("");
  const state = useBusy();

  const load = async (rescan = false) => {
    try {
      await init();
      setStrings(S);
      const result = await working(rescan ? t("busy_scan") : t("busy_load"), () => overviewCall(rescan));
      setData(result);
      setError("");
    } catch (e) {
      setError(String(e));
    }
  };
  const refresh = () => { load(false); };

  useEffect(() => {
    load(false);
    const listener = addEventListener<[name: string, done: number, total: number]>(
      "download_progress", (name, done, total) => {
        setBusy({
          text: t("busy_download_progress", {
            name, done: Math.round(done / 1e6), total: Math.round(total / 1e6),
          }),
          progress: total > 0 ? (100 * done) / total : -1,
        });
      });
    return () => { removeEventListener("download_progress", listener); };
  }, []);

  const running = data?.games.filter((g) => g.running) ?? [];
  const others = data?.games.filter((g) => !g.running) ?? [];
  void strings;

  return (
    <>
      {state.text && (
        <PanelSection>
          <PanelSectionRow>
            <ProgressBarWithInfo indeterminate={state.progress < 0} nProgress={Math.max(0, state.progress)}
              sOperationText={state.text} />
          </PanelSectionRow>
        </PanelSection>
      )}
      {error && (
        <PanelSection><PanelSectionRow><div style={muted}>{error}</div></PanelSectionRow></PanelSection>
      )}
      {running.length > 0 && (
        <PanelSection title={t("deck_running")}>
          {running.map((game) => <GameRow key={game.app_id} game={game} refresh={refresh} />)}
        </PanelSection>
      )}
      <PanelSection title={t("deck_games")}>
        {data && data.outdated > 0 && (
          <PanelSectionRow>
            <ButtonItem layout="below" disabled={!!state.text} onClick={async () => {
              let result = await working(t("busy_update_all"), () => updateAllCall());
              if (!result.ok && result.kind === "download" && result.keys) {
                if (!(await ask(t("dl_title"), result.message, t("dl_confirm_ok")))) return;
                const fetched = await download(result.keys);
                if (!fetched.ok) { await report(fetched); return; }
                result = await working(t("busy_update_all"), () => updateAllCall());
              }
              await report(result);
              refresh();
            }}>{t("btn_update_all", { count: data.outdated })}</ButtonItem>
          </PanelSectionRow>
        )}
        {others.map((game) => <GameRow key={game.app_id} game={game} refresh={refresh} />)}
        {data && data.games.length === 0 && (
          <PanelSectionRow><div style={muted}>{t("deck_no_games")}</div></PanelSectionRow>
        )}
        {data && data.unsupported > 0 && (
          <PanelSectionRow><div style={muted}>{t("deck_unsupported", { count: data.unsupported })}</div></PanelSectionRow>
        )}
        <PanelSectionRow>
          <ButtonItem layout="below" disabled={!!state.text} onClick={() => load(true)}>
            {t("rescan")}
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>
      {data && (
        <PanelSection title={t("deck_setup")}>
          <PanelSectionRow>
            <ButtonItem layout="below" label={data.helixsr.pill}
              description={data.helixsr.message || data.helixsr.path}
              onClick={async () => {
                try {
                  const picked = await openFilePicker(1 as never, data.helixsr.path || data.home, false, true);
                  const result = await setHelixsrFolder(picked.realpath || picked.path);
                  if (!result.ok) await report(result);
                } catch (e) { /* picker closed */ }
                refresh();
              }}>
              {t("btn_choose_folder")}
            </ButtonItem>
          </PanelSectionRow>
          <PanelSectionRow>
            <ButtonItem layout="below" label={data.downloads.missing.length ? t("dl_pill_partly") : t("dl_all_ready")}
              description={data.gpu}
              onClick={() => showModal(<DownloadsModal downloads={data.downloads} refresh={refresh} />)}>
              {t("deck_downloads")}
            </ButtonItem>
          </PanelSectionRow>
          <PanelSectionRow>
            <ToggleField label={t("deck_toast")} description={t("deck_toast_tip")} checked={data.toast}
              onChange={async (value) => { toastEnabled = value; await setToast(value); refresh(); }} />
          </PanelSectionRow>
          <PanelSectionRow>
            <DropdownItem label={t("language")}
              rgOptions={[{ data: "", label: t("deck_language_steam") },
                ...data.languages.map(([data, label]) => ({ data, label }))]}
              selectedOption={data.language}
              onChange={async (option) => {
                const result = await setLanguageCall(option.data);
                S = result.strings;
                setStrings(S);
                refresh();
              }} />
          </PanelSectionRow>
          <PanelSectionRow>
            <div style={muted}>Scaler Assistant v{data.version}</div>
          </PanelSectionRow>
        </PanelSection>
      )}
    </>
  );
}

// ---- notification when a game starts -------------------------------------------------------

const WATCH_SECONDS = 90;

async function watchGame(appId: number) {
  await init();
  if (!toastEnabled) return;
  const started = Date.now();
  while (Date.now() - started < WATCH_SECONDS * 1000) {
    await new Promise((r) => setTimeout(r, 5000));
    let game: Game | null = null;
    try { game = await runtimeCall(appId); } catch (e) { return; }
    if (!game || !game.running) return;   // no upscaler from Scaler Assistant, or game closed
    const late = Date.now() - started >= (WATCH_SECONDS - 5) * 1000;
    if (game.running.loaded || late) {
      toaster.toast({ title: game.name, body: game.running.headline });
      return;
    }
  }
}

export default definePlugin(() => {
  init().catch(() => { ready = null; });
  const lifetime = SteamClient.GameSessions.RegisterForAppLifetimeNotifications((n) => {
    if (n.bRunning) watchGame(n.unAppID);
  });
  return {
    name: "Scaler Assistant",
    titleView: <div className={staticClasses.Title}>Scaler Assistant</div>,
    content: <Content />,
    icon: <FaLayerGroup />,
    onDismount() {
      lifetime.unregister();
    },
  };
});
